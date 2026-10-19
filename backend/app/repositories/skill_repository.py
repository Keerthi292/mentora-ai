"""Database access for skills. No HTTP or business rules here, only queries.

Every skill belongs to one user; all queries are filtered by user_id.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Skill


def list_skills(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Skill]:
    stmt = select(Skill).where(Skill.user_id == user_id).order_by(Skill.name).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def get_skill(db: Session, skill_id: int, user_id: int) -> Skill | None:
    stmt = select(Skill).where(Skill.id == skill_id, Skill.user_id == user_id)
    return db.scalars(stmt).first()


def get_skill_by_name(db: Session, name: str, user_id: int) -> Skill | None:
    # Case-insensitive, so "python" counts as a duplicate of "Python"
    stmt = select(Skill).where(Skill.user_id == user_id, func.lower(Skill.name) == name.lower())
    return db.scalars(stmt).first()


def lowercase_names(db: Session, user_id: int) -> set[str]:
    """The user's skill names, lowercased (for quick "already saved?" checks)."""
    return set(db.scalars(select(func.lower(Skill.name)).where(Skill.user_id == user_id)))


def create_skill(db: Session, user_id: int, data: dict) -> Skill:
    skill = Skill(user_id=user_id, **data)
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
