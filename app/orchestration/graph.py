
import unicodedata

from langgraph.graph import StateGraph, START, END

from app.orchestration.state import AgentState
from app.agents.router_agent import RouterAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.customer_support_agent import CustomerSupportAgent


CONFIDENCE_THRESHOLD = 0.65


def normalize_text(text: str) -> str:
    """Normaliza texto para facilitar a identificação de solicitações."""

    normalized = unicodedata.normalize("NFKD", text.lower())

    return "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    )


def should_handoff(state: AgentState) -> str:
    """Identifica solicitações explícitas de atendimento humano."""

    message = normalize_text(state.get("message", ""))

    handoff_phrases = [
        "falar com atendente",
        "falar com um atendente",
        "falar com uma pessoa",
        "atendimento humano",
        "atendente humano",
        "quero um atendente",
        "quero falar com humano",
        "quero falar com uma pessoa",
        "transferir para atendente",
        "me transfira",
        "falar com alguem",
        "pessoa real",
    ]

    if any(phrase in message for phrase in handoff_phrases):
        return "handoff"

    return "router"


def router_node(state: AgentState) -> dict:
    """Classifica a mensagem e registra a decisão."""

    router = RouterAgent()
    decision = router.route(state["message"])

    return {
        "intent": decision.intent,
        "target_agent": decision.target_agent,
        "confidence": decision.confidence,
    }


def route_next(state: AgentState) -> str:
    """Define qual agente receberá a solicitação."""

    if state.get("confidence", 0) < CONFIDENCE_THRESHOLD:
        return "fallback"

    if state.get("intent") == "unknown":
        return "fallback"

    target = state.get("target_agent", "fallback")

    if target not in ("knowledge", "customer_support"):
        return "fallback"

    return target


def knowledge_node(state: AgentState) -> dict:
    """Executa o agente de conhecimento."""

    result = KnowledgeAgent().run(state["message"])

    return {
        "response": result.get("response", ""),
        "status": result.get("status", "success"),
        "tools_used": result.get("tools_used", []),
        "sources": result.get("sources", []),
        **(
            {"error": result["error"]}
            if result.get("error")
            else {}
        ),
    }


def customer_support_node(state: AgentState) -> dict:
    """Executa o agente de atendimento ao cliente."""

    agent = CustomerSupportAgent()

    result = agent.run(
        message=state["message"],
        user_id=state.get("user_id", ""),
    )

    return {
        "response": result.get("response", ""),
        "status": result.get("status", "success"),
        "tools_used": result.get("tools_used", []),
        "sources": result.get("sources", []),
        **(
            {"error": result["error"]}
            if result.get("error")
            else {}
        ),
    }


def human_handoff_node(state: AgentState) -> dict:
    """Sinaliza que a solicitação precisa de atendimento humano."""

    return {
        "response": (
            "Entendi que você deseja falar com um atendente humano. "
            "Sua solicitação foi identificada para encaminhamento. "
            "No momento, este canal ainda não está conectado "
            "a uma fila de atendimento humano."
        ),
        "status": "handoff_required",
        "target_agent": "human_handoff",
        "tools_used": [],
        "sources": [],
    }


def fallback_node(state: AgentState) -> dict:
    """Responde quando não é possível identificar a intenção."""

    return {
        "response": (
            "Não consegui identificar sua solicitação. "
            "Poderia explicar um pouco melhor?"
        ),
        "status": "success",
        "tools_used": [],
        "sources": [],
    }


def build_graph():
    """Constrói e compila o fluxo multiagente."""

    workflow = StateGraph(AgentState)

    workflow.add_node("router", router_node)
    workflow.add_node("knowledge", knowledge_node)
    workflow.add_node("customer_support", customer_support_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("human_handoff", human_handoff_node)

    workflow.add_conditional_edges(
        START,
        should_handoff,
        {
            "handoff": "human_handoff",
            "router": "router",
        },
    )

    workflow.add_conditional_edges(
        "router",
        route_next,
        {
            "knowledge": "knowledge",
            "customer_support": "customer_support",
            "fallback": "fallback",
        },
    )

    workflow.add_edge("knowledge", END)
    workflow.add_edge("customer_support", END)
    workflow.add_edge("fallback", END)
    workflow.add_edge("human_handoff", END)

    return workflow.compile()


graph = build_graph()
