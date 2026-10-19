"""Tests for accounts and logins (/api/auth/*), the session cookie, the account
command (app/manage.py) and the MCP token check. These use `anon_client`, which
follows the real login rules (no test shortcut)."""

import asyncio
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import SecretStr

from app import manage
from app.config import settings
from app.dependencies import SESSION_COOKIE
from app.mcp_server import RequireMcpToken
from app.models import LoginSession, User
from app.security import hash_password, token_hash, verify_password

ME = "/api/me"
KEERTHI = {"full_name": "Keerthi", "email": "Keerthi@Example.com", "password": "correct horse 1"}


def register(client, **changes):
    return client.post("/api/auth/register", json={**KEERTHI, **changes})


# --- Passwords -----------------------------------------------------------------------


def test_password_hashes():
    stored = hash_password("s3cret pass")

    assert stored.startswith("scrypt$") and "s3cret" not in stored
    assert stored != hash_password("s3cret pass")  # random salt
    assert verify_password("s3cret pass", stored)
    assert not verify_password("wrong pass", stored)
    assert not verify_password("s3cret pass", None)
    assert not verify_password("s3cret pass", "garbage")


# --- Sign up -------------------------------------------------------------------------


def test_register_creates_an_account_and_logs_in(anon_client, db):
    response = register(anon_client)

    assert response.status_code == 201
    assert response.json()["email"] == "keerthi@example.com"  # stored lowercase
    cookie = response.headers["set-cookie"]
    assert SESSION_COOKIE in cookie and "HttpOnly" in cookie and "samesite=lax" in cookie.lower()
    assert anon_client.get(ME).json()["full_name"] == "Keerthi"

    user = db.query(User).one()
    assert user.password_hash and KEERTHI["password"] not in user.password_hash
    # Only the token's hash is stored
    session = db.query(LoginSession).one()
    assert session.id == token_hash(anon_client.cookies[SESSION_COOKIE])


def test_register_same_email_returns_409(anon_client):
    register(anon_client)
    anon_client.cookies.clear()

    response = register(anon_client, email="  KEERTHI@example.COM ")

    assert response.status_code == 409


@pytest.mark.parametrize(
    "changes",
    [{"email": "not-an-email"}, {"password": "short"}, {"full_name": "  "}, {"password": "x" * 129}],
)
def test_register_invalid_input_returns_422(anon_client, changes):
    assert register(anon_client, **changes).status_code == 422


# --- Log in / log out ----------------------------------------------------------------


def test_login_and_logout(anon_client, db):
    register(anon_client)
    anon_client.cookies.clear()
    assert anon_client.get(ME).status_code == 401

    response = anon_client.post("/api/auth/login", json={"email": "keerthi@example.com", "password": KEERTHI["password"]})
    assert response.status_code == 200
    assert anon_client.get(ME).status_code == 200

    assert anon_client.post("/api/auth/logout").status_code == 204
    assert anon_client.get(ME).status_code == 401
    assert db.query(LoginSession).count() == 1  # only the sign-up session is left


@pytest.mark.parametrize(
    "login",
    [
        {"email": "keerthi@example.com", "password": "wrong password"},
        {"email": "nobody@example.com", "password": KEERTHI["password"]},
    ],
)
def test_wrong_login_gives_the_same_401(anon_client, login):
    register(anon_client)
    anon_client.cookies.clear()

    response = anon_client.post("/api/auth/login", json=login)

    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong email or password."
    assert SESSION_COOKIE not in response.headers.get("set-cookie", "")


def test_account_without_password_cannot_log_in(anon_client, demo_user):
    response = anon_client.post("/api/auth/login", json={"email": demo_user.email, "password": "anything123"})
    assert response.status_code == 401


# --- The session cookie ---------------------------------------------------------------


@pytest.mark.parametrize(
    "path", ["/api/me", "/api/skills", "/api/projects", "/api/conversations", "/api/dashboard", "/api/ai/tip"]
)
def test_endpoints_need_a_login(anon_client, path):
    response = anon_client.get(path)
    assert response.status_code == 401
    assert response.json()["detail"] == "Please log in."


def test_forged_cookie_is_rejected(anon_client):
    anon_client.cookies.set(SESSION_COOKIE, "made-up-token")
    assert anon_client.get(ME).status_code == 401


def test_expired_session_is_rejected(anon_client, db):
    register(anon_client)
    session = db.query(LoginSession).one()
    session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    assert anon_client.get(ME).status_code == 401


def test_each_account_sees_only_its_own_data(anon_client):
    register(anon_client)
    anon_client.post("/api/skills", json={"name": "Python"})
    anon_client.post("/api/projects", json={"name": "Mentora"})
    anon_client.post("/api/auth/logout")

    register(anon_client, email="friend@example.com", full_name="Friend")

    assert anon_client.get("/api/skills").json() == []
    assert anon_client.get("/api/projects").json() == []
    assert anon_client.get(ME).json()["full_name"] == "Friend"


# --- python -m app.manage set-login ---------------------------------------------------


def test_set_login_gives_an_old_account_a_password(anon_client, db, demo_user, monkeypatch):
    monkeypatch.setattr(manage, "SessionLocal", lambda: nullcontext(db))
    monkeypatch.setattr(manage.getpass, "getpass", lambda prompt: "my new password")

    manage.set_login(demo_user.id, "Me@Example.com")

    assert demo_user.email == "me@example.com"
    response = anon_client.post("/api/auth/login", json={"email": "me@example.com", "password": "my new password"})
    assert response.status_code == 200


def test_set_login_refuses_mismatched_passwords(db, demo_user, monkeypatch):
    answers = iter(["first password", "second password"])
    monkeypatch.setattr(manage, "SessionLocal", lambda: nullcontext(db))
    monkeypatch.setattr(manage.getpass, "getpass", lambda prompt: next(answers))

    with pytest.raises(SystemExit, match="don't match"):
        manage.set_login(demo_user.id, "me@example.com")
    assert demo_user.password_hash is None


# --- MCP token ------------------------------------------------------------------------


def _call_mcp(headers: dict[bytes, bytes], path: str = "/mcp") -> int:
    """Status code of a request through RequireMcpToken (the real MCP app isn't needed)."""
    sent = []

    async def inner(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})

    async def send(message):
        sent.append(message)

    scope = {"type": "http", "path": path, "headers": list(headers.items())}
    asyncio.run(RequireMcpToken(inner)(scope, None, send))
    return sent[0]["status"]


def test_mcp_needs_the_token(monkeypatch):
    monkeypatch.setattr(settings, "MCP_TOKEN", SecretStr("the-token"))

    assert _call_mcp({b"authorization": b"Bearer the-token"}) == 200
    assert _call_mcp({b"authorization": b"Bearer wrong"}) == 401
    assert _call_mcp({}) == 401
    # Other paths are not MCP's business
    assert _call_mcp({}, path="/something-else") == 200


def test_mcp_is_closed_without_a_configured_token(monkeypatch):
    monkeypatch.setattr(settings, "MCP_TOKEN", None)
    assert _call_mcp({b"authorization": b"Bearer "}) == 401
