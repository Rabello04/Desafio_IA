
from pathlib import Path

from google import genai
from google.genai import types

from app.config import settings
from app.tools.sales import get_sales
from app.tools.payouts import get_payout_date


class CustomerSupportAgent:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY não configurada.")

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.model = settings.GEMINI_MODEL

        prompt_path = (
            Path(__file__).resolve().parents[1]
            / "prompts"
            / "customer_support.txt"
        )

        self.system_instruction = prompt_path.read_text(
            encoding="utf-8"
        )

        self.available_tools = {
            "get_sales": get_sales,
            "get_payout_date": get_payout_date,
        }

        self.tool_declarations = [
            types.FunctionDeclaration(
                name="get_sales",
                description=(
                    "Consulta todas as vendas registradas "
                    "para o cliente autenticado."
                ),
            ),
            types.FunctionDeclaration(
                name="get_payout_date",
                description=(
                    "Consulta os valores e as datas previstas "
                    "de recebimento do cliente autenticado."
                ),
            ),
        ]

    def run(self, message: str, user_id: str) -> dict:
        """Processa a solicitação e executa ferramentas quando necessário."""

        if not user_id:
            return {
                "response": "Não foi possível identificar o cliente.",
                "status": "error",
                "tools_used": [],
                "sources": [],
            }

        try:
            tool = types.Tool(
                function_declarations=self.tool_declarations
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        self.system_instruction
                        + f"\n\nCliente autenticado: {user_id}"
                        + "\nUtilize esse cliente para todas as consultas."
                    ),
                    tools=[tool],
                ),
            )

            if not response.candidates:
                raise RuntimeError(
                    "O Gemini não retornou uma resposta válida."
                )

            model_content = response.candidates[0].content

            function_calls = [
                part.function_call
                for part in (model_content.parts or [])
                if part.function_call
            ]

            if not function_calls:
                return {
                    "response": response.text or (
                        "Não consegui gerar uma resposta."
                    ),
                    "status": "success",
                    "tools_used": [],
                    "sources": [],
                }

            function_responses = []
            tools_used = []

            for function_call in function_calls:
                function_name = function_call.name

                if function_name not in self.available_tools:
                    result = {
                        "error": "Ferramenta não disponível."
                    }
                else:
                    result = self.available_tools[function_name](
                        user_id
                    )
                    tools_used.append(function_name)

                function_responses.append(
                    types.Part.from_function_response(
                        name=function_name,
                        response={"result": result},
                    )
                )

            final_response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=message)],
                    ),
                    model_content,
                    types.Content(
                        role="user",
                        parts=function_responses,
                    ),
                ],
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                ),
            )

            return {
                "response": final_response.text or (
                    "Consultei as informações, mas não consegui "
                    "formular uma resposta."
                ),
                "status": "success",
                "tools_used": list(dict.fromkeys(tools_used)),
                "sources": [],
            }

        except Exception as error:
            return {
                "response": (
                    "Não foi possível consultar suas informações "
                    "no momento."
                ),
                "status": "error",
                "tools_used": [],
                "sources": [],
                "error": str(error),
            }
