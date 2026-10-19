"""A status report printed in the terminal when the backend starts, so you can
see at a glance what works and what doesn't:

    INFO:     ── Mentora AI ──────────────────────────────────────
    INFO:     ✓ Database    connected to mentora on localhost:5432
    INFO:     ✓ Migrations  up to date (909b0d3d06d8)
    ...

Every check catches its own errors: a failed check prints ✗ with a hint and the
backend keeps starting.
"""

import logging
from collections.abc import Callable
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from app.config import BACKEND_DIR, settings
from app.models import Conversation, LearningGoal, Project, Skill, User

logger = logging.getLogger(__name__)

OK, FAIL = "✓", "✗"


class _UvicornStyle(logging.Formatter):
    """"INFO:     message", like uvicorn's own lines."""

    def format(self, record: logging.LogRecord) -> str:
        return f"{record.levelname + ':':<9} {super().format(record)}"


def setup_logging() -> None:
    """Show the app's own log lines (logger "app" and below) in the terminal."""
    app_logger = logging.getLogger("app")
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_UvicornStyle("%(message)s"))
        app_logger.addHandler(handler)
        app_logger.setLevel(logging.INFO)
        app_logger.propagate = False


def _database(engine: Engine) -> str:
    url = engine.url
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as exc:
        raise RuntimeError(
            f"can't connect to {url.database} on {url.host}:{url.port}. "
            "Is PostgreSQL running? Try: docker start mentora-postgres"
        ) from exc
    return f"connected to {url.database} on {url.host}:{url.port}"


def _migrations(engine: Engine) -> str:
    head = ScriptDirectory.from_config(Config(BACKEND_DIR / "alembic.ini")).get_current_head()
    with engine.connect() as conn:
        current = MigrationContext.configure(conn).get_current_revision()
    if current != head:
        raise RuntimeError(f"database is on {current or 'nothing'}, code needs {head}. Run: uv run alembic upgrade head")
    return f"up to date ({head})"


def _user(engine: Engine) -> str:
    with Session(engine) as db:
        user = db.get(User, settings.DEMO_USER_ID)
    if user is None:
        raise RuntimeError(f"user {settings.DEMO_USER_ID} not found. Run: uv run python -m app.seed")
    return f'"{user.full_name}" (id {user.id})'


def _data(engine: Engine) -> str:
    with Session(engine) as db:
        count = lambda model: db.scalar(select(func.count()).select_from(model))  # noqa: E731
        return (
            f"{count(Skill)} skills, {count(LearningGoal)} learning goals, "
            f"{count(Project)} projects, {count(Conversation)} chats"
        )


def _gemini() -> str:
    key = settings.GEMINI_API_KEY.get_secret_value().strip() if settings.GEMINI_API_KEY else ""
    if not key:
        raise RuntimeError("GEMINI_API_KEY is missing in backend/.env: the AI features won't work")
    return f"key set, model {settings.GEMINI_MODEL} (not called now, to save quota)"


def _uploads() -> str:
    folder = Path(settings.UPLOAD_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    probe = folder / ".write-test"
    probe.write_text("ok")
    probe.unlink()
    files = sum(1 for f in folder.iterdir() if f.is_file())
    return f"{folder} ({files} files, max {settings.MAX_UPLOAD_MB} MB each)"


def _mcp(tools: list[str]) -> str:
    if not tools:
        raise RuntimeError("no MCP tools registered")
    return f"/mcp, tools: {', '.join(tools)}"


def _line(label: str, check: Callable[[], str]) -> bool:
    try:
        logger.info("%s %-11s %s", OK, label, check())
        return True
    except Exception as exc:
        logger.warning("%s %-11s %s", FAIL, label, str(exc).splitlines()[0] or type(exc).__name__)
        return False


def print_startup_report(engine: Engine, mcp_tools: list[str]) -> bool:
    """Log one line per part of the backend. Returns True if everything is OK."""
    logger.info("── Mentora AI " + "─" * 46)
    results = [_line("Database", lambda: _database(engine))]
    if results[0]:
        results += [
            _line("Migrations", lambda: _migrations(engine)),
            _line("User", lambda: _user(engine)),
            _line("Data", lambda: _data(engine)),
        ]
    else:
        logger.warning("%s %-11s skipped (no database)", FAIL, "Migrations, user, data")
    results += [
        _line("Gemini", _gemini),
        _line("Uploads", _uploads),
        _line("MCP", lambda: _mcp(mcp_tools)),
    ]
    ok = all(results)
    logger.info("── %s · API docs at /docs " + "─" * 22, "All systems ready" if ok else "Started with problems (see ✗ above)")
    return ok
