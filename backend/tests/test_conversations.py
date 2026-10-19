"""Tests for /api/conversations (mentor chats saved in the database)."""

import pytest

from app.models import ChatMessage, Conversation, User

URL = "/api/conversations"

pytestmark = pytest.mark.usefixtures("demo_user")

FILE = {"id": "a" * 32, "filename": "shot.png", "content_type": "image/png", "size": 10, "url": "/api/uploads/" + "a" * 32}


def chat(title="Learn React", messages=None, **extra):
    if messages is None:
        messages = [
            {"id": "m1", "role": "user", "content": "How do I learn React?  ", "attachments": [FILE]},
            {"id": "m2", "role": "assistant", "content": "Start with the docs."},
        ]
    return {"title": title, "messages": messages, **extra}


def test_save_and_load_a_chat(client):
    response = client.put(f"{URL}/c-1", json=chat())

    assert response.status_code == 200
    assert response.json()["id"] == "c-1"
    assert response.json()["title"] == "Learn React"

    loaded = client.get(f"{URL}/c-1").json()
    assert loaded["messages"] == [
        # Text is kept exactly, including trailing spaces
        {"id": "m1", "role": "user", "content": "How do I learn React?  ", "attachments": [FILE],
         "error": None, "stopped": False, "edited": False},
        {"id": "m2", "role": "assistant", "content": "Start with the docs.", "attachments": [],
         "error": None, "stopped": False, "edited": False},
    ]


def test_saving_again_replaces_the_messages(client, db):
    client.put(f"{URL}/c-1", json=chat())
    edited = [
        {"id": "m1", "role": "user", "content": "How do I learn Vue?", "edited": True},
        {"id": "m3", "role": "assistant", "content": "", "error": "Quota used up"},
        {"id": "m4", "role": "assistant", "content": "Half a rep", "stopped": True},
    ]

    client.put(f"{URL}/c-1", json=chat(messages=edited))

    messages = client.get(f"{URL}/c-1").json()["messages"]
    assert [(m["id"], m["edited"], m["error"], m["stopped"]) for m in messages] == [
        ("m1", True, None, False),
        ("m3", False, "Quota used up", False),
        ("m4", False, None, True),
    ]
    assert db.query(ChatMessage).count() == 3


def test_list_is_newest_first_without_messages(client):
    client.put(f"{URL}/old", json=chat("Old", updated_at="2026-01-01T10:00:00Z"))
    client.put(f"{URL}/new", json=chat("New", updated_at="2026-02-01T10:00:00Z"))

    body = client.get(URL).json()

    assert [c["title"] for c in body] == ["New", "Old"]
    assert "messages" not in body[0]
    assert body[1]["updated_at"].startswith("2026-01-01T10:00:00")


def test_rename_keeps_messages_and_time(client):
    saved = client.put(f"{URL}/c-1", json=chat()).json()

    response = client.patch(f"{URL}/c-1", json={"title": "  React plan  "})

    assert response.json()["title"] == "React plan"
    assert response.json()["updated_at"] == saved["updated_at"]
    assert len(client.get(f"{URL}/c-1").json()["messages"]) == 2


def test_delete_removes_chat_and_messages(client, db):
    client.put(f"{URL}/c-1", json=chat())

    assert client.delete(f"{URL}/c-1").status_code == 204
    assert client.get(f"{URL}/c-1").status_code == 404
    assert db.query(ChatMessage).count() == 0


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_unknown_chat_returns_404(client, method):
    kwargs = {"json": {"title": "x"}} if method == "patch" else {}
    assert getattr(client, method)(f"{URL}/nope", **kwargs).status_code == 404


def test_other_users_chats_are_hidden_and_protected(client, db, make_user):
    other = make_user()
    db.add(Conversation(id="theirs", user_id=other.id, title="Private"))
    db.commit()

    assert client.get(URL).json() == []
    assert client.get(f"{URL}/theirs").status_code == 404
    # Can't overwrite, rename or delete it either
    assert client.put(f"{URL}/theirs", json=chat()).status_code == 404
    assert client.patch(f"{URL}/theirs", json={"title": "Mine"}).status_code == 404
    assert client.delete(f"{URL}/theirs").status_code == 404
    assert db.get(Conversation, "theirs").title == "Private"


@pytest.mark.parametrize(
    "body",
    [
        chat(title=""),
        chat(title="x" * 81),
        chat(messages=[{"id": "m1", "role": "system", "content": "hi"}]),
        chat(messages=[{"id": "bad id!", "role": "user", "content": "hi"}]),
        chat(messages=[{"id": "m1", "role": "user", "attachments": [{**FILE, "id": "../x"}]}]),
        chat(messages=[{"id": "m1", "role": "user", "attachments": [FILE] * 6}]),
    ],
)
def test_invalid_chats_return_422(client, body):
    assert client.put(f"{URL}/c-1", json=body).status_code == 422


def test_invalid_chat_id_returns_422(client):
    assert client.put(f"{URL}/bad%20id", json=chat()).status_code == 422


def test_chats_need_the_user(client, db):
    db.query(User).delete()
    db.commit()
    assert client.get(URL).status_code == 404
    assert client.put(f"{URL}/c-1", json=chat()).status_code == 404
