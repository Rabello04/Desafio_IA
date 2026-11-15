
from typing import TypedDict


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

    # Resposta final
    response: str
    status: str
    error: str
