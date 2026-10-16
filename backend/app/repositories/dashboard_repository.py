"""Database queries for the dashboard summary. No HTTP or business rules here, only queries."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import LearningGoal, Skill


def count_skills(db: Session) -> int:
    # Skills are a shared catalog (no owner), the same list the Skills page shows
    return db.scalar(select(func.count()).select_from(Skill))


def count_by_status(db: Session, model, user_id: int) -> dict[str, int]:
    """{status: count} of the user's rows in a table that has user_id and status."""
    stmt = select(model.status, func.count()).where(model.user_id == user_id).group_by(model.status)
    return dict(db.execute(stmt).all())


def list_goals_with_progress(db: Session, user_id: int, limit: int) -> list[LearningGoal]:
    # Load each goal's progress entries in one extra query instead of one per goal
    stmt = (
        select(LearningGoal)
        .where(LearningGoal.user_id == user_id, LearningGoal.status != "abandoned")
        .options(selectinload(LearningGoal.progress_entries))
        .order_by(LearningGoal.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))
