"""Tests for POST /api/ai/chat (mock LLM)."""


def test_chat_returns_reply(client):
    response = client.post("/api/ai/chat", json={"message": "How do I learn FastAPI?"})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["response"], str)
    assert body["response"] != ""


def test_chat_empty_message_returns_422(client):
    response = client.post("/api/ai/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_whitespace_only_message_returns_422(client):
    # Whitespace is stripped first, so this counts as empty
    response = client.post("/api/ai/chat", json={"message": "   "})
    assert response.status_code == 422


def test_chat_missing_message_returns_422(client):
    response = client.post("/api/ai/chat", json={})
    assert response.status_code == 422
