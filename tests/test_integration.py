
from types import SimpleNamespace

import app.orchestration.graph as graph_module


def test_integration_knowledge_agent(monkeypatch):
    """Verifica o roteamento para o Knowledge Agent."""

    class FakeRouter:
        def route(self, message):
            return SimpleNamespace(
                intent="knowledge",
                target_agent="knowledge",
                confidence=0.95,
            )

    class FakeKnowledgeAgent:
        def run(self, message):
            return {
                "response": "Resposta simulada sobre produtos Getnet.",
                "status": "success",
                "tools_used": [],
                "sources": [],
            }

    monkeypatch.setattr(graph_module, "RouterAgent", FakeRouter)
    monkeypatch.setattr(graph_module, "KnowledgeAgent", FakeKnowledgeAgent)

    result = graph_module.graph.invoke({
        "message": "Quais são os produtos da Getnet?",
        "user_id": "user_001",
    })

    assert result["target_agent"] == "knowledge"
    assert result["response"] == "Resposta simulada sobre produtos Getnet."
    assert result["status"] == "success"


def test_integration_customer_support_agent(monkeypatch):
    """Verifica o roteamento para o Customer Support Agent."""

    class FakeRouter:
        def route(self, message):
            return SimpleNamespace(
                intent="customer_support",
                target_agent="customer_support",
                confidence=0.95,
            )

    class FakeCustomerSupportAgent:
        def run(self, message, user_id):
            return {
                "response": f"Vendas simuladas do cliente {user_id}.",
                "status": "success",
                "tools_used": ["get_sales"],
                "sources": [],
            }

    monkeypatch.setattr(graph_module, "RouterAgent", FakeRouter)
    monkeypatch.setattr(
        graph_module,
        "CustomerSupportAgent",
        FakeCustomerSupportAgent,
    )

    result = graph_module.graph.invoke({
        "message": "Quais foram minhas vendas?",
        "user_id": "user_001",
    })

    assert result["target_agent"] == "customer_support"
    assert "user_001" in result["response"]
    assert "get_sales" in result["tools_used"]


def test_integration_human_handoff():
    """Verifica se o pedido de atendimento humano ignora o roteador."""

    result = graph_module.graph.invoke({
        "message": "Quero falar com um atendente humano.",
        "user_id": "user_001",
    })

    assert result["status"] == "handoff_required"
    assert result["target_agent"] == "human_handoff"
    assert result["tools_used"] == []


def test_integration_fallback(monkeypatch):
    """Verifica o fallback quando a intenção não é reconhecida."""

    class FakeRouter:
        def route(self, message):
            return SimpleNamespace(
                intent="unknown",
                target_agent="fallback",
                confidence=0.20,
            )

    monkeypatch.setattr(graph_module, "RouterAgent", FakeRouter)

    result = graph_module.graph.invoke({
        "message": "Uma solicitação sem intenção identificada.",
        "user_id": "user_001",
    })

    assert result["response"] == (
        "Não consegui identificar sua solicitação. "
        "Poderia explicar um pouco melhor?"
    )
    assert result["tools_used"] == []
