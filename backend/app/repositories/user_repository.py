"""Database access for users (only what other modules need for now)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def user_exists(db: Session, user_id: int) -> bool:
    return db.get(User, user_id) is not None


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def update_user(db: Session, user: User, changes: dict) -> User:
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email.lower())).first()


def create_user(db: Session, data: dict) -> User:
    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
