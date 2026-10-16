"""Database access for learning goals. No HTTP or business rules here, only queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import LearningGoal


def list_goals(
    db: Session, user_id: int, status: str | None = None, skip: int = 0, limit: int = 100
) -> list[LearningGoal]:
    # Load progress updates in one extra query (the response includes the latest one)
    stmt = (
        select(LearningGoal)
        .where(LearningGoal.user_id == user_id)
        .options(selectinload(LearningGoal.progress_entries))
    )
    if status is not None:
        stmt = stmt.where(LearningGoal.status == status)
    stmt = stmt.order_by(LearningGoal.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def get_goal(db: Session, goal_id: int, user_id: int) -> LearningGoal | None:
    # Filter by user_id too, so users can only see their own goals
    stmt = select(LearningGoal).where(
        LearningGoal.id == goal_id, LearningGoal.user_id == user_id
    )
    return db.scalars(stmt).first()


def create_goal(db: Session, user_id: int, data: dict) -> LearningGoal:
    goal = LearningGoal(user_id=user_id, **data)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, goal: LearningGoal, changes: dict) -> LearningGoal:
    for field, value in changes.items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, goal: LearningGoal) -> None:
    db.delete(goal)
    db.commit()
