
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings


class RouterDecision(BaseModel):
    intent: Literal[
        "product_information",
        "payment_information",
        "account_information",
        "technical_support",
        "general_information",
        "unknown",
    ]

    target_agent: Literal[
        "knowledge",
        "customer_support",
        "fallback",
    ]

    confidence: float = Field(ge=0.0, le=1.0)


ROUTER_PROMPT = """
Você é o Router Agent de um sistema de atendimento da Getnet.

Sua responsabilidade é identificar a intenção da mensagem
e encaminhá-la ao agente adequado.

Agentes disponíveis:

1. knowledge:
   Informações sobre produtos, serviços, pagamentos,
   dúvidas gerais e suporte técnico da Getnet.
   Também pode realizar pesquisas na web.

2. customer_support:
   Solicitações que dependem de informações individuais
   do cliente, como histórico de vendas e situação de repasses.

3. fallback:
   Mensagens ambíguas, incompletas ou sem intenção identificável.

Classifique a mensagem em uma destas intenções:

- product_information
- payment_information
- account_information
- technical_support
- general_information
- unknown

Regras importantes:

- Perguntas gerais sobre contas e recebimentos vão para knowledge.
- Consultas sobre dados específicos de um cliente vão para
  customer_support.
- Problemas técnicos com produtos Getnet vão para knowledge.
- Perguntas sobre informações atuais, como câmbio e clima,
  vão para knowledge.
- Não invente informações.
- Se não conseguir identificar a intenção, use unknown
  e encaminhe para fallback.
- A confiança deve refletir o quanto a classificação é segura.
"""


class RouterAgent:

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY não foi configurada no arquivo .env"
            )

        if not settings.GEMINI_MODEL:
            raise ValueError(
                "GEMINI_MODEL não foi configurado no arquivo .env"
            )

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.model = settings.GEMINI_MODEL

    def route(self, message: str) -> RouterDecision:

        response = self.client.models.generate_content(
            model=self.model,
            contents=(
                f"{ROUTER_PROMPT}\n\n"
                f"Mensagem do usuário:\n{message}"
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RouterDecision,
                temperature=0,
            ),
        )

        if response.parsed is not None:
            return response.parsed

        if not response.text:
            raise ValueError(
                "O Gemini não retornou uma classificação válida."
            )

        return RouterDecision.model_validate_json(response.text)
