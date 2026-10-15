"""Database access for skills. No HTTP or business rules here, only queries."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Skill


def list_skills(db: Session, skip: int = 0, limit: int = 100) -> list[Skill]:
    stmt = select(Skill).order_by(Skill.name).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def get_skill(db: Session, skill_id: int) -> Skill | None:
    return db.get(Skill, skill_id)


def get_skill_by_name(db: Session, name: str) -> Skill | None:
    # Case-insensitive, so "python" counts as a duplicate of "Python"
    stmt = select(Skill).where(func.lower(Skill.name) == name.lower())
    return db.scalars(stmt).first()


def create_skill(db: Session, data: dict) -> Skill:
    skill = Skill(**data)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


def update_skill(db: Session, skill: Skill, changes: dict) -> Skill:
    for field, value in changes.items():
        setattr(skill, field, value)
    db.commit()
    db.refresh(skill)
    return skill


def delete_skill(db: Session, skill: Skill) -> None:
    db.delete(skill)
    db.commit()
