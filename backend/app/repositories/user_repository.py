"""Database access for users (only what other modules need for now)."""

from sqlalchemy.orm import Session

from app.models import User


def user_exists(db: Session, user_id: int) -> bool:
    return db.get(User, user_id) is not None
