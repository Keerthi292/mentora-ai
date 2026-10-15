"""Shared user checks used by every service that works with a user's data."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import user_repository


def ensure_user_exists(db: Session, user_id: int) -> None:
    if not user_repository.user_exists(db, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
