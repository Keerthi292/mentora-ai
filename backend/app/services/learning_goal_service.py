"""Business rules for learning goals: user/goal existence and ownership checks."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import LearningGoal
from app.repositories import learning_goal_repository
from app.schemas import LearningGoalCreate, LearningGoalUpdate
from app.services import user_service


def list_goals(
    db: Session, user_id: int, goal_status: str | None, skip: int, limit: int
) -> list[LearningGoal]:
    user_service.ensure_user_exists(db, user_id)
    return learning_goal_repository.list_goals(db, user_id, goal_status, skip, limit)


def get_goal(db: Session, goal_id: int, user_id: int) -> LearningGoal:
    # A goal owned by another user is reported as "not found" on purpose,
    # so the API never reveals other users' data.
    goal = learning_goal_repository.get_goal(db, goal_id, user_id)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Learning goal not found"
        )
    return goal


def create_goal(db: Session, user_id: int, payload: LearningGoalCreate) -> LearningGoal:
    user_service.ensure_user_exists(db, user_id)
    return learning_goal_repository.create_goal(db, user_id, payload.model_dump())


def update_goal(
    db: Session, goal_id: int, user_id: int, payload: LearningGoalUpdate
) -> LearningGoal:
    goal = get_goal(db, goal_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    return learning_goal_repository.update_goal(db, goal, changes)


def delete_goal(db: Session, goal_id: int, user_id: int) -> None:
    goal = get_goal(db, goal_id, user_id)
    learning_goal_repository.delete_goal(db, goal)
