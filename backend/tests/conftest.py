"""Shared pytest fixtures.

Tests use a SEPARATE PostgreSQL database (mentora_test by default), so your
dev data in `mentora` is never touched. Override it with TEST_DATABASE_URL.

How isolation works:
- Once per test run: create the test database if needed, and create all tables.
- For every test: open a transaction, run the test inside it, then roll it back.
  So each test starts with empty tables, and tests can't affect each other.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, get_db
from app.dependencies import get_current_user_id
from app.main import app
from app.models import User

# Same server and credentials as the dev database, but a different database name
_dev_url = make_url(settings.database_url)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    _dev_url.set(database="mentora_test").render_as_string(hide_password=False),
)

# Tests create and drop tables, so never run them against a hosted database (e.g. Neon)
# by accident. Set TEST_DATABASE_URL to use another server on purpose.
if not os.getenv("TEST_DATABASE_URL") and _dev_url.host not in ("localhost", "127.0.0.1", "::1"):
    pytest.exit(
        f"DATABASE_URL points to {_dev_url.host}, not this computer. The tests won't create "
        "tables there. Point DATABASE_URL at your local database, or set TEST_DATABASE_URL.",
        returncode=2,
    )


def _create_test_database_if_missing() -> None:
    test_db_name = make_url(TEST_DATABASE_URL).database
    # CREATE DATABASE can't run inside a transaction, hence AUTOCOMMIT
    admin_engine = create_engine(_dev_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": test_db_name}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def engine():
    _create_test_database_if_missing()
    engine = create_engine(TEST_DATABASE_URL)
    # Start each run from a clean schema that matches the current models
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def no_real_gemini(monkeypatch):
    """Never call the real Gemini API from tests (no key needed, no quota used).

    Tests that need a reply use the `fake_gemini` fixture in test_ai_chat.py.
    """
    from pydantic import SecretStr

    from app.ai import llm_client

    def _refuse(*args, **kwargs):
        raise AssertionError("Tests must not call the real Gemini API; use the fake_gemini fixture.")

    monkeypatch.setattr(settings, "GEMINI_API_KEY", SecretStr("test-key-not-real"))
    monkeypatch.setattr(llm_client, "_create_client", _refuse)


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    """Uploaded files go to a temporary folder, never backend/uploads."""
    folder = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", folder)
    return folder


@pytest.fixture
def db(engine):
    """A session whose changes are rolled back after the test.

    The services call db.commit(); with join_transaction_mode="create_savepoint"
    those commits only release a savepoint, and the outer transaction is still
    rolled back at the end.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# The user `client` acts as (see the demo_user fixture)
DEMO_USER_ID = 1


@pytest.fixture
def anon_client(db):
    """A TestClient that uses the test session and is NOT logged in (real login rules)."""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    # Not used as `with TestClient(app)`, so the MCP lifespan doesn't start
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client(anon_client):
    """A TestClient logged in as the demo user (id 1), so the feature tests don't
    each need to log in. Login itself is tested with `anon_client` in test_auth.py."""
    app.dependency_overrides[get_current_user_id] = lambda: DEMO_USER_ID
    return anon_client


@pytest.fixture
def demo_user(db) -> User:
    """The user `client` acts as: id 1, "Demo User"."""
    user = User(id=DEMO_USER_ID, email="demo@mentora.local", full_name="Demo User")
    db.add(user)
    db.commit()
    # The id was chosen by hand, so move PostgreSQL's id counter past it
    db.execute(text("SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT max(id) FROM users))"))
    return user


@pytest.fixture
def make_user(db):
    """Factory: make_user() inserts ANOTHER user (not the demo user) and returns it.

    Useful for checking that the demo user can't see other people's data.
    """
    counter = {"n": 0}

    def _make_user(full_name: str = "Test User") -> User:
        counter["n"] += 1
        user = User(email=f"user{counter['n']}@example.com", full_name=full_name)
        db.add(user)
        db.commit()
        return user

    return _make_user
