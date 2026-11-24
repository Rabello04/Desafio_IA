from typing import TypedDict


class TokenUsage(TypedDict, total=False):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class AgentState(TypedDict, total=False):
    # Entrada do usuário
    message: str
    user_id: str

    # Classificação do Router
    intent: str
    target_agent: str
    confidence: float

    # Contexto e resultados
    context: str
    sources: list[str]
    tools_used: list[str]

    # Consumo acumulado de tokens nesta interação
    token_usage: TokenUsage

    # Resposta final
    response: str
    status: str
    error: str
