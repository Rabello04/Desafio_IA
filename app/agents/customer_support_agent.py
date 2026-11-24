
from pathlib import Path

from google import genai
from google.genai import types

from app.config import settings
from app.tools.sales import get_sales
from app.tools.payouts import get_payout_date


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

        token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

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

            token_usage = extract_token_usage(response)

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
                    "token_usage": token_usage,
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

            final_usage = extract_token_usage(final_response)
            token_usage = {
                "input_tokens": token_usage["input_tokens"] + final_usage["input_tokens"],
                "output_tokens": token_usage["output_tokens"] + final_usage["output_tokens"],
                "total_tokens": token_usage["total_tokens"] + final_usage["total_tokens"],
            }

            return {
                "response": final_response.text or (
                    "Consultei as informações, mas não consegui "
                    "formular uma resposta."
                ),
                "status": "success",
                "tools_used": list(dict.fromkeys(tools_used)),
                "sources": [],
                "token_usage": token_usage,
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
                "token_usage": token_usage,
                "error": str(error),
            }
