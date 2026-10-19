"""Tests for GET / PATCH /api/me (the current user's name)."""

from app.ai import agent
from app.seed import DEMO_USER_EMAIL, DEMO_USER_NAME


def test_get_me_returns_the_demo_user(client, demo_user):
    response = client.get("/api/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": demo_user.id,
        "full_name": DEMO_USER_NAME,
        "email": DEMO_USER_EMAIL,
        "theme": "dark",
    }


def test_rename_me(client, demo_user):
    response = client.patch("/api/me", json={"full_name": "  Keerthi  "})

    assert response.status_code == 200
    assert response.json()["full_name"] == "Keerthi"
    assert client.get("/api/me").json()["full_name"] == "Keerthi"


def test_change_theme(client, demo_user):
    assert client.patch("/api/me", json={"theme": "light"}).json()["theme"] == "light"
    assert client.get("/api/me").json()["theme"] == "light"
    assert client.patch("/api/me", json={"theme": "blue"}).status_code == 422


def test_rename_me_with_nothing_changes_nothing(client, demo_user):
    assert client.patch("/api/me", json={}).json()["full_name"] == DEMO_USER_NAME


def test_rename_me_invalid_names_return_422(client, demo_user):
    for body in ({"full_name": ""}, {"full_name": "   "}, {"full_name": None}, {"full_name": "x" * 256}):
        assert client.patch("/api/me", json=body).status_code == 422


def test_me_without_the_demo_user_returns_404(client):
    assert client.get("/api/me").status_code == 404
    assert client.patch("/api/me", json={"full_name": "Keerthi"}).status_code == 404


def test_mentor_knows_the_new_name(client, demo_user, monkeypatch):
    client.patch("/api/me", json={"full_name": "Keerthi"})
    calls = []

    def fake_generate(system_prompt, *args, **kwargs):
        calls.append(system_prompt)
        return "Hi Keerthi!"

    monkeypatch.setattr(agent, "generate_response", fake_generate)

    client.post("/api/ai/chat", json={"message": "hi"})

    assert "Name: Keerthi" in calls[0]
