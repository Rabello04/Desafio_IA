
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import routes


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_chat_endpoint_success(client, monkeypatch):
    expected_result = {
        "response": "A Getnet oferece diferentes maquininhas.",
        "status": "success",
        "intent": "product_information",
        "target_agent": "knowledge",
        "tools_used": ["gemini_file_search"],
        "sources": [],
    }

    def mock_invoke(state):
        assert state["message"] == "Quais maquininhas a Getnet oferece?"
        assert state["user_id"] == "user_001"
        return expected_result

    monkeypatch.setattr(routes.graph, "invoke", mock_invoke)

    response = client.post(
        "/chat",
        json={
            "message": "Quais maquininhas a Getnet oferece?",
            "user_id": "user_001",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["target_agent"] == "knowledge"


def test_chat_endpoint_rejects_empty_message(client):
    response = client.post(
        "/chat",
        json={
            "message": "",
            "user_id": "user_001",
        },
    )

    assert response.status_code == 422


def test_chat_endpoint_requires_user_id(client):
    response = client.post(
        "/chat",
        json={
            "message": "Quais são minhas vendas?",
        },
    )

    assert response.status_code == 422
