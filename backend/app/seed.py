"""Create the demo user the app uses while there is no authentication.

Safe to run many times: if a user with DEMO_USER_ID already exists, nothing changes.

Runs automatically on app startup (see main.py). To run it by hand:
    cd backend && .venv/bin/python -m app.seed
"""

import logging

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

DEMO_USER_NAME = "Demo User"
DEMO_USER_EMAIL = "demo@mentora.local"


def seed_demo_user(db: Session) -> bool:
    """Insert the demo user if missing. Returns True if it was created."""
    user_id = settings.DEMO_USER_ID

    # INSERT ... ON CONFLICT DO NOTHING: if the id (or email) already exists,
    # PostgreSQL skips the insert instead of raising an error. This is also
    # safe if two app processes start at the same time.
    stmt = (
        insert(User)
        .values(id=user_id, full_name=DEMO_USER_NAME, email=DEMO_USER_EMAIL)
        .on_conflict_do_nothing()
    )
    created = db.execute(stmt).rowcount == 1

    if created:
        # We chose the id ourselves, so PostgreSQL's id counter didn't move.
        # Move it past the highest id, or the next new user would also get id 1.
        db.execute(
            text("SELECT setval(pg_get_serial_sequence('users', 'id'), :max_id)"),
            {"max_id": db.scalar(select(func.max(User.id)))},
        )
    db.commit()

    if db.get(User, user_id) is None:
        # Only possible if another user already has the demo email
        logger.warning(
            "Demo user %s was not created: email %s is already used by another user",
            user_id,
            DEMO_USER_EMAIL,
        )
    return created


def run_seed() -> None:
    """Open a session, seed, and close it. Used by main.py and the CLI."""
    with SessionLocal() as db:
        if seed_demo_user(db):
            logger.info("Created demo user (id=%s)", settings.DEMO_USER_ID)
        else:
            logger.info("Demo user check done (id=%s), nothing to create", settings.DEMO_USER_ID)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    run_seed()
