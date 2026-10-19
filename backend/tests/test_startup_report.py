"""Tests for the startup report (app/startup_report.py) and the MCP tool log lines."""

import logging

import pytest
from pydantic import SecretStr
from sqlalchemy import create_engine

from app.config import settings
from app.mcp_server import ping
from app.startup_report import print_startup_report


@pytest.fixture
def app_log():
    """The app's log lines (logger "app" doesn't pass them on to pytest's own capture)."""
    lines = []
    handler = logging.Handler()
    handler.emit = lambda record: lines.append(record.getMessage())
    logger = logging.getLogger("app")
    logger.addHandler(handler)
    yield lines
    logger.removeHandler(handler)


@pytest.fixture
def mcp_settings(monkeypatch):
    monkeypatch.setattr(settings, "MCP_TOKEN", SecretStr("test-mcp-token"))
    monkeypatch.setattr(settings, "MCP_USER_ID", 1)


def test_report_with_a_working_database(engine, app_log, mcp_settings):
    ok = print_startup_report(engine, ["ask_mentor", "ping"])

    text = "\n".join(app_log)
    assert "✓ Database    connected to mentora_test" in text
    assert "✓ Data" in text
    assert "✓ Gemini" in text  # the tests set a fake key
    # The test database is empty (each test's rows are rolled back)
    assert "✗ Users       0 accounts, none can log in yet. Sign up in the app" in text
    assert "✗ MCP         MCP_USER_ID=1 doesn't exist" in text
    # The test database is made without Alembic, so this one is expected to fail
    assert "✗ Migrations" in text
    assert ok is False


def test_report_when_the_database_is_down(app_log, mcp_settings):
    down = create_engine("postgresql+psycopg2://nobody:x@127.0.0.1:1/none")

    assert print_startup_report(down, ["ping"]) is False

    text = "\n".join(app_log)
    assert "✗ Database" in text and "docker start mentora-postgres" in text
    assert "skipped (no database)" in text
    assert "✓ MCP         /mcp (Bearer token), acts as user 1 (not checked: no database)" in text
    assert "Started with problems" in app_log[-1]


def test_report_without_gemini_key_or_mcp_tools(engine, monkeypatch, app_log, mcp_settings):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", SecretStr(" "))

    print_startup_report(engine, [])

    text = "\n".join(app_log)
    assert "✗ Gemini      GEMINI_API_KEY is missing" in text
    assert "✗ MCP         no MCP tools registered" in text


def test_mcp_tool_calls_are_logged(app_log):
    assert ping() == "Mentora AI MCP server is running"
    assert app_log[0] == "MCP ▶ ping called"
    assert app_log[1].startswith("MCP ✓ ping done in")
