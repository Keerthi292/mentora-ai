from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas import (
    UserSkillCreate,
    UserSkillResponse,
    UserSkillStatus,
    UserSkillUpdate,
)
from app.services import user_skill_service

router = APIRouter(prefix="/api/user-skills", tags=["User Skills"])


@router.get("", response_model=list[UserSkillResponse])
def list_user_skills(
    user_id: int = Depends(get_current_user_id),
    skill_status: UserSkillStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return user_skill_service.list_user_skills(db, user_id, skill_status, skip, limit)


@router.post("", response_model=UserSkillResponse, status_code=status.HTTP_201_CREATED)
def create_user_skill(
    payload: UserSkillCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return user_skill_service.create_user_skill(db, user_id, payload)


@router.get("/{user_skill_id}", response_model=UserSkillResponse)
def get_user_skill(
    user_skill_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return user_skill_service.get_user_skill(db, user_skill_id, user_id)


@router.patch("/{user_skill_id}", response_model=UserSkillResponse)
def update_user_skill(
    user_skill_id: int,
    payload: UserSkillUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return user_skill_service.update_user_skill(db, user_skill_id, user_id, payload)


@router.delete("/{user_skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_skill(
    user_skill_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    user_skill_service.delete_user_skill(db, user_skill_id, user_id)
