from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas import (
    CareerGoalCreate,
    CareerGoalResponse,
    CareerGoalStatus,
    CareerGoalUpdate,
)
from app.services import career_goal_service

router = APIRouter(prefix="/api/career-goals", tags=["Career Goals"])


@router.get("", response_model=list[CareerGoalResponse])
def list_career_goals(
    user_id: int = Depends(get_current_user_id),
    goal_status: CareerGoalStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return career_goal_service.list_career_goals(db, user_id, goal_status, skip, limit)


@router.post("", response_model=CareerGoalResponse, status_code=status.HTTP_201_CREATED)
def create_career_goal(
    payload: CareerGoalCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return career_goal_service.create_career_goal(db, user_id, payload)


@router.get("/{career_goal_id}", response_model=CareerGoalResponse)
def get_career_goal(
    career_goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return career_goal_service.get_career_goal(db, career_goal_id, user_id)


@router.patch("/{career_goal_id}", response_model=CareerGoalResponse)
def update_career_goal(
    career_goal_id: int,
    payload: CareerGoalUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return career_goal_service.update_career_goal(db, career_goal_id, user_id, payload)


@router.delete("/{career_goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_career_goal(
    career_goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    career_goal_service.delete_career_goal(db, career_goal_id, user_id)
