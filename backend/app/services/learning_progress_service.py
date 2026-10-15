"""Business rules for learning progress.

Progress entries belong to a learning goal, so every function first checks
that the goal exists AND belongs to the user (reusing learning_goal_service).
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import LearningProgress
from app.repositories import learning_progress_repository
from app.schemas import LearningProgressCreate, LearningProgressUpdate
from app.services import learning_goal_service


def list_progress(
    db: Session, goal_id: int, user_id: int, skip: int, limit: int
) -> list[LearningProgress]:
    learning_goal_service.get_goal(db, goal_id, user_id)  # 404 if not the user's goal
    return learning_progress_repository.list_progress(db, goal_id, skip, limit)


def get_progress(db: Session, progress_id: int, goal_id: int, user_id: int) -> LearningProgress:
    learning_goal_service.get_goal(db, goal_id, user_id)
    entry = learning_progress_repository.get_progress(db, progress_id, goal_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Progress entry not found"
        )
    return entry


def create_progress(
    db: Session, goal_id: int, user_id: int, payload: LearningProgressCreate
) -> LearningProgress:
    learning_goal_service.get_goal(db, goal_id, user_id)
    return learning_progress_repository.create_progress(db, goal_id, payload.model_dump())


def update_progress(
    db: Session, progress_id: int, goal_id: int, user_id: int, payload: LearningProgressUpdate
) -> LearningProgress:
    entry = get_progress(db, progress_id, goal_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    return learning_progress_repository.update_progress(db, entry, changes)


def delete_progress(db: Session, progress_id: int, goal_id: int, user_id: int) -> None:
    entry = get_progress(db, progress_id, goal_id, user_id)
    learning_progress_repository.delete_progress(db, entry)
