"""Business rules for skills: not-found checks and duplicate-name checks."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Skill
from app.repositories import skill_repository
from app.schemas import SkillCreate, SkillUpdate


def _duplicate_name_error(name: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"A skill named '{name}' already exists",
    )


def list_skills(db: Session, skip: int, limit: int) -> list[Skill]:
    return skill_repository.list_skills(db, skip, limit)


def get_skill(db: Session, skill_id: int) -> Skill:
    skill = skill_repository.get_skill(db, skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


def create_skill(db: Session, payload: SkillCreate) -> Skill:
    if skill_repository.get_skill_by_name(db, payload.name):
        raise _duplicate_name_error(payload.name)
    try:
        return skill_repository.create_skill(db, payload.model_dump())
    except IntegrityError:
        # Another request created the same name at the same moment
        db.rollback()
        raise _duplicate_name_error(payload.name)


def update_skill(db: Session, skill_id: int, payload: SkillUpdate) -> Skill:
    skill = get_skill(db, skill_id)
    # exclude_unset: only change the fields the client actually sent
    changes = payload.model_dump(exclude_unset=True)

    new_name = changes.get("name")
    if new_name is not None:
        existing = skill_repository.get_skill_by_name(db, new_name)
        if existing is not None and existing.id != skill.id:
            raise _duplicate_name_error(new_name)
    try:
        return skill_repository.update_skill(db, skill, changes)
    except IntegrityError:
        db.rollback()
        raise _duplicate_name_error(new_name)


def delete_skill(db: Session, skill_id: int) -> None:
    skill = get_skill(db, skill_id)
    skill_repository.delete_skill(db, skill)
