"""Business rules for career goals: user/goal existence and ownership checks."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import CareerGoal
from app.repositories import career_goal_repository
from app.schemas import CareerGoalCreate, CareerGoalUpdate
from app.services import user_service


def list_career_goals(
    db: Session, user_id: int, goal_status: str | None, skip: int, limit: int
) -> list[CareerGoal]:
    user_service.ensure_user_exists(db, user_id)
    return career_goal_repository.list_career_goals(db, user_id, goal_status, skip, limit)


def get_career_goal(db: Session, career_goal_id: int, user_id: int) -> CareerGoal:
    # Another user's goal is reported as "not found" on purpose
    career_goal = career_goal_repository.get_career_goal(db, career_goal_id, user_id)
    if career_goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Career goal not found"
        )
    return career_goal


def create_career_goal(db: Session, user_id: int, payload: CareerGoalCreate) -> CareerGoal:
    user_service.ensure_user_exists(db, user_id)
    return career_goal_repository.create_career_goal(db, user_id, payload.model_dump())


def update_career_goal(
    db: Session, career_goal_id: int, user_id: int, payload: CareerGoalUpdate
) -> CareerGoal:
    career_goal = get_career_goal(db, career_goal_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    return career_goal_repository.update_career_goal(db, career_goal, changes)


def delete_career_goal(db: Session, career_goal_id: int, user_id: int) -> None:
    career_goal = get_career_goal(db, career_goal_id, user_id)
    career_goal_repository.delete_career_goal(db, career_goal)
