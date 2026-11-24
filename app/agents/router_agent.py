
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings


def extract_token_usage(response) -> dict:
    """Lê os tokens informados pela própria resposta do Gemini."""
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
    output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
    total_tokens = int(
        getattr(usage, "total_token_count", 0)
        or (input_tokens + output_tokens)
    )
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


class RouterDecision(BaseModel):
    intent: Literal[
        "product_information",
        "payment_information",
        "account_information",
        "technical_support",
        "general_information",
        "external_information",
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
   Responde perguntas sobre produtos, serviços, pagamentos,
   informações gerais e dúvidas externas à Getnet.

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
- external_information
- unknown

Regras de classificação:

- Perguntas sobre produtos, serviços, taxas e soluções Getnet:
  product_information.

- Perguntas gerais sobre pagamentos e recebimentos Getnet:
  payment_information.

- Consultas sobre dados específicos de um cliente:
  account_information, encaminhando para customer_support.

- Problemas técnicos relacionados aos produtos Getnet:
  technical_support.

- Perguntas que dependem de informações atuais, como câmbio,
  clima, notícias ou dados recentes:
  general_information, encaminhando para knowledge.

- Perguntas externas e de conhecimento geral que não dependem
  de informações atuais, como receitas, curiosidades, conceitos,
  cálculos e conhecimentos cotidianos:
  external_information, encaminhando para knowledge.

- Não classifique perguntas externas como assuntos da Getnet
  apenas porque foram feitas dentro deste sistema.

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
        self.last_token_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

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

        self.last_token_usage = extract_token_usage(response)

        if response.parsed is not None:
            return response.parsed

        if not response.text:
            raise ValueError(
                "O Gemini não retornou uma classificação válida."
            )

        return RouterDecision.model_validate_json(response.text)
