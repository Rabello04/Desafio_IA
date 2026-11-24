
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import routes


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/auth/login",
        json={
            "username": "user_001",
            "password": "Getnet@2026-001",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_login_success(client):
    response = client.post(
        "/auth/login",
        json={
            "username": "user_001",
            "password": "Getnet@2026-001",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rejects_invalid_password(client):
    response = client.post(
        "/auth/login",
        json={
            "username": "user_001",
            "password": "senha-errada",
        },
    )

    assert response.status_code == 401


def test_chat_requires_authentication(client):
    response = client.post(
        "/chat",
        json={"message": "Olá"},
    )

    assert response.status_code == 401


def test_chat_endpoint_success(client, auth_headers, monkeypatch):
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
        json={"message": "Quais maquininhas a Getnet oferece?"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["target_agent"] == "knowledge"


def test_chat_rejects_user_id_in_request_body(client, auth_headers):
    response = client.post(
        "/chat",
        json={
            "message": "Olá",
            "user_id": "user_002",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_chat_rejects_empty_message(client, auth_headers):
    response = client.post(
        "/chat",
        json={"message": ""},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_chat_uses_authenticated_customer(client, monkeypatch):
    login = client.post(
        "/auth/login",
        json={
            "username": "user_002",
            "password": "Getnet@2026-002",
        },
    )

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    def mock_invoke(state):
        assert state["user_id"] == "user_002"
        return {
            "response": "Consulta realizada.",
            "status": "success",
        }

    monkeypatch.setattr(routes.graph, "invoke", mock_invoke)

    response = client.post(
        "/chat",
        json={"message": "Quais são minhas vendas?"},
        headers=headers,
    )

    assert response.status_code == 200
