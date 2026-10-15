from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas import (
    LearningGoalCreate,
    LearningGoalResponse,
    LearningGoalStatus,
    LearningGoalUpdate,
)
from app.services import learning_goal_service

router = APIRouter(prefix="/api/learning-goals", tags=["Learning Goals"])


@router.get("", response_model=list[LearningGoalResponse])
def list_goals(
    user_id: int = Depends(get_current_user_id),
    goal_status: LearningGoalStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return learning_goal_service.list_goals(db, user_id, goal_status, skip, limit)


@router.post("", response_model=LearningGoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: LearningGoalCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return learning_goal_service.create_goal(db, user_id, payload)


@router.get("/{goal_id}", response_model=LearningGoalResponse)
def get_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return learning_goal_service.get_goal(db, goal_id, user_id)


@router.patch("/{goal_id}", response_model=LearningGoalResponse)
def update_goal(
    goal_id: int,
    payload: LearningGoalUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return learning_goal_service.update_goal(db, goal_id, user_id, payload)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    learning_goal_service.delete_goal(db, goal_id, user_id)
