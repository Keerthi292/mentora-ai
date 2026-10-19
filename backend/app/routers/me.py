from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas import UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/api/me", tags=["Me"])


@router.get("", response_model=UserResponse)
def get_me(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """The user making the request (for now always the demo user)."""
    return user_service.get_user(db, user_id)


@router.patch("", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Change your name. The app and the mentor greet you with it."""
    return user_service.update_user(db, user_id, payload)
