"""Database access for learning progress. No HTTP or business rules here, only queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LearningProgress


def list_progress(
    db: Session, learning_goal_id: int, skip: int = 0, limit: int = 100
) -> list[LearningProgress]:
    # Oldest first, so the list reads like a timeline
    stmt = (
        select(LearningProgress)
        .where(LearningProgress.learning_goal_id == learning_goal_id)
        .order_by(LearningProgress.created_at, LearningProgress.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def get_progress(
    db: Session, progress_id: int, learning_goal_id: int
) -> LearningProgress | None:
    # Filter by goal too, so an entry is only reachable through its own goal
    stmt = select(LearningProgress).where(
        LearningProgress.id == progress_id,
        LearningProgress.learning_goal_id == learning_goal_id,
    )
    return db.scalars(stmt).first()


def create_progress(db: Session, learning_goal_id: int, data: dict) -> LearningProgress:
    entry = LearningProgress(learning_goal_id=learning_goal_id, **data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_progress(db: Session, entry: LearningProgress, changes: dict) -> LearningProgress:
    for field, value in changes.items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete_progress(db: Session, entry: LearningProgress) -> None:
    db.delete(entry)
    db.commit()
