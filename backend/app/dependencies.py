"""Shared FastAPI dependencies."""

from app.config import settings


def get_current_user_id() -> int:
    """Return the id of the user making the request.

    For now the app has no login, so this is always the demo user
    (created on startup by app/seed.py).
    """
    # Replace this with real authentication later.
    return settings.DEMO_USER_ID
