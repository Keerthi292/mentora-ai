"""Business rules for user skills: existence, ownership, and duplicate checks."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import UserSkill
from app.repositories import skill_repository, user_skill_repository
from app.schemas import UserSkillCreate, UserSkillUpdate
from app.services import user_service


def _already_added_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This user already has this skill",
    )


def list_user_skills(
    db: Session, user_id: int, skill_status: str | None, skip: int, limit: int
) -> list[UserSkill]:
    user_service.ensure_user_exists(db, user_id)
    return user_skill_repository.list_user_skills(db, user_id, skill_status, skip, limit)


def get_user_skill(db: Session, user_skill_id: int, user_id: int) -> UserSkill:
    # Another user's entry is reported as "not found" on purpose
    user_skill = user_skill_repository.get_user_skill(db, user_skill_id, user_id)
    if user_skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User skill not found"
        )
    return user_skill


def create_user_skill(db: Session, user_id: int, payload: UserSkillCreate) -> UserSkill:
    user_service.ensure_user_exists(db, user_id)
    if skill_repository.get_skill(db, payload.skill_id, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    if user_skill_repository.get_by_user_and_skill(db, user_id, payload.skill_id):
        raise _already_added_error()
    try:
        return user_skill_repository.create_user_skill(db, user_id, payload.model_dump())
    except IntegrityError:
        # Another request added the same skill at the same moment
        db.rollback()
        raise _already_added_error()


def update_user_skill(
    db: Session, user_skill_id: int, user_id: int, payload: UserSkillUpdate
) -> UserSkill:
    user_skill = get_user_skill(db, user_skill_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    return user_skill_repository.update_user_skill(db, user_skill, changes)


def delete_user_skill(db: Session, user_skill_id: int, user_id: int) -> None:
    user_skill = get_user_skill(db, user_skill_id, user_id)
    user_skill_repository.delete_user_skill(db, user_skill)
