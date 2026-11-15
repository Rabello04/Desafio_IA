
from fastapi.testclient import TestClient

from app.main import app
from app.api import routes


def test_guardrails(monkeypatch):
    client = TestClient(app)

    # 1. Simula uma resposta válida sem chamar o Gemini
    def mock_invoke(state):
        return {
            "response": "Solicitação processada.",
            "status": "success",
            "intent": "general_information",
            "target_agent": "knowledge",
            "tools_used": [],
            "sources": [],
        }

    monkeypatch.setattr(routes.graph, "invoke", mock_invoke)

    # 2. Mensagem válida deve ser aceita
    valid = client.post(
        "/chat",
        json={
            "message": "Olá, gostaria de informações.",
            "user_id": "user_001",
        },
    )
    assert valid.status_code == 200

    # 3. Mensagem vazia deve ser rejeitada
    empty = client.post(
        "/chat",
        json={
            "message": "   ",
            "user_id": "user_001",
        },
    )
    assert empty.status_code == 422

    # 4. Mensagem acima de 2000 caracteres deve ser rejeitada
    oversized = client.post(
        "/chat",
        json={
            "message": "A" * 2001,
            "user_id": "user_001",
        },
    )
    assert oversized.status_code == 422

    # 5. Identificador vazio deve ser rejeitado
    missing_user = client.post(
        "/chat",
        json={
            "message": "Olá",
            "user_id": "",
        },
    )
    assert missing_user.status_code == 422

    # 6. Campos extras devem ser rejeitados
    extra_field = client.post(
        "/chat",
        json={
            "message": "Olá",
            "user_id": "user_001",
            "admin": True,
        },
    )
    assert extra_field.status_code == 422

    # 7. Erros internos não devem expor detalhes técnicos
    def simulate_error(state):
        raise RuntimeError("INTERNAL_SECRET_ERROR")

    monkeypatch.setattr(routes.graph, "invoke", simulate_error)

    error = client.post(
        "/chat",
        json={
            "message": "Olá",
            "user_id": "user_001",
        },
    )

    assert error.status_code == 500
    assert "INTERNAL_SECRET_ERROR" not in error.text
    assert "Não foi possível processar" in error.text

    print("\nTodos os 6 cenários de Guardrails foram aprovados!")
