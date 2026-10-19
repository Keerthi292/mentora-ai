"""Shared user checks used by every service that works with a user's data."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.repositories import user_repository
from app.schemas import UserUpdate


def ensure_user_exists(db: Session, user_id: int) -> None:
    if not user_repository.user_exists(db, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


def get_user(db: Session, user_id: int) -> User:
    user = user_repository.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def update_user(db: Session, user_id: int, payload: UserUpdate) -> User:
    user = get_user(db, user_id)
    return user_repository.update_user(db, user, payload.model_dump(exclude_unset=True))
