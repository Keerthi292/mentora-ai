"""Database access for career goals. No HTTP or business rules here, only queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CareerGoal


def list_career_goals(
    db: Session, user_id: int, status: str | None = None, skip: int = 0, limit: int = 100
) -> list[CareerGoal]:
    stmt = select(CareerGoal).where(CareerGoal.user_id == user_id)
    if status is not None:
        stmt = stmt.where(CareerGoal.status == status)
    stmt = stmt.order_by(CareerGoal.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def get_career_goal(db: Session, career_goal_id: int, user_id: int) -> CareerGoal | None:
    # Filter by user_id too, so users can only see their own goals
    stmt = select(CareerGoal).where(
        CareerGoal.id == career_goal_id, CareerGoal.user_id == user_id
    )
    return db.scalars(stmt).first()


def create_career_goal(db: Session, user_id: int, data: dict) -> CareerGoal:
    career_goal = CareerGoal(user_id=user_id, **data)
    db.add(career_goal)
    db.commit()
    db.refresh(career_goal)
    return career_goal


def update_career_goal(db: Session, career_goal: CareerGoal, changes: dict) -> CareerGoal:
    for field, value in changes.items():
        setattr(career_goal, field, value)
    db.commit()
    db.refresh(career_goal)
    return career_goal


def delete_career_goal(db: Session, career_goal: CareerGoal) -> None:
    db.delete(career_goal)
    db.commit()
