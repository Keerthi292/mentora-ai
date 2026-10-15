from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas import (
    LearningProgressCreate,
    LearningProgressResponse,
    LearningProgressUpdate,
)
from app.services import learning_progress_service

# Progress entries live under their learning goal in the URL,
# e.g. /api/learning-goals/5/progress
router = APIRouter(
    prefix="/api/learning-goals/{goal_id}/progress", tags=["Learning Progress"]
)


@router.get("", response_model=list[LearningProgressResponse])
def list_progress(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return learning_progress_service.list_progress(db, goal_id, user_id, skip, limit)


@router.post("", response_model=LearningProgressResponse, status_code=status.HTTP_201_CREATED)
def create_progress(
    goal_id: int,
    payload: LearningProgressCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return learning_progress_service.create_progress(db, goal_id, user_id, payload)


@router.get("/{progress_id}", response_model=LearningProgressResponse)
def get_progress(
    goal_id: int,
    progress_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return learning_progress_service.get_progress(db, progress_id, goal_id, user_id)


@router.patch("/{progress_id}", response_model=LearningProgressResponse)
def update_progress(
    goal_id: int,
    progress_id: int,
    payload: LearningProgressUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return learning_progress_service.update_progress(db, progress_id, goal_id, user_id, payload)


@router.delete("/{progress_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_progress(
    goal_id: int,
    progress_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    learning_progress_service.delete_progress(db, progress_id, goal_id, user_id)
