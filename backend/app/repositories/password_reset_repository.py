"""Database access for "forgot password" links. No HTTP or business rules here, only queries."""

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import LoginSession, PasswordReset


def replace_reset(db: Session, reset_id: str, user_id: int, expires_at: datetime) -> PasswordReset:
    """Store a new link for the user; their older links stop working."""
    db.execute(delete(PasswordReset).where(PasswordReset.user_id == user_id))
    reset = PasswordReset(id=reset_id, user_id=user_id, expires_at=expires_at)
    db.add(reset)
    db.commit()
    return reset


def get_valid_reset(db: Session, reset_id: str) -> PasswordReset | None:
    stmt = select(PasswordReset).where(
        PasswordReset.id == reset_id, PasswordReset.expires_at > datetime.now(timezone.utc)
    )
    return db.scalars(stmt).first()


def delete_resets_and_sessions(db: Session, user_id: int) -> None:
    """After a reset: every link and every login of the user ends (no commit; the caller commits)."""
    db.execute(delete(PasswordReset).where(PasswordReset.user_id == user_id))
    db.execute(delete(LoginSession).where(LoginSession.user_id == user_id))
