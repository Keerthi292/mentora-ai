"""Database access for "forgot password" codes. No HTTP or business rules here, only queries."""

from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import LoginSession, PasswordReset


def replace_reset(db: Session, user_id: int, code_hash: str, expires_at: datetime) -> PasswordReset:
    """Store a new code for the user; their older code stops working."""
    db.execute(delete(PasswordReset).where(PasswordReset.user_id == user_id))
    reset = PasswordReset(user_id=user_id, code_hash=code_hash, expires_at=expires_at)
    db.add(reset)
    db.commit()
    return reset


def get_reset(db: Session, user_id: int) -> PasswordReset | None:
    return db.get(PasswordReset, user_id)


def count_wrong_try(db: Session, reset: PasswordReset, max_attempts: int) -> None:
    """One more wrong code; after max_attempts the code is deleted."""
    reset.attempts += 1
    if reset.attempts >= max_attempts:
        db.delete(reset)
    db.commit()


def delete_reset(db: Session, reset: PasswordReset) -> None:
    db.delete(reset)
    db.commit()


def delete_reset_and_sessions(db: Session, user_id: int) -> None:
    """After a reset: the code and every login of the user end (no commit; the caller commits)."""
    db.execute(delete(PasswordReset).where(PasswordReset.user_id == user_id))
    db.execute(delete(LoginSession).where(LoginSession.user_id == user_id))
