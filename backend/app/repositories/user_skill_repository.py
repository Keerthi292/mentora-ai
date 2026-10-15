"""Database access for user skills. No HTTP or business rules here, only queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import UserSkill


def list_user_skills(
    db: Session, user_id: int, status: str | None = None, skip: int = 0, limit: int = 100
) -> list[UserSkill]:
    stmt = (
        select(UserSkill)
        .where(UserSkill.user_id == user_id)
        # Load each entry's skill in one extra query instead of one per row
        .options(selectinload(UserSkill.skill))
    )
    if status is not None:
        stmt = stmt.where(UserSkill.status == status)
    stmt = stmt.order_by(UserSkill.id).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def get_user_skill(db: Session, user_skill_id: int, user_id: int) -> UserSkill | None:
    # Filter by user_id too, so users can only see their own entries
    stmt = select(UserSkill).where(
        UserSkill.id == user_skill_id, UserSkill.user_id == user_id
    )
    return db.scalars(stmt).first()


def get_by_user_and_skill(db: Session, user_id: int, skill_id: int) -> UserSkill | None:
    stmt = select(UserSkill).where(
        UserSkill.user_id == user_id, UserSkill.skill_id == skill_id
    )
    return db.scalars(stmt).first()


def create_user_skill(db: Session, user_id: int, data: dict) -> UserSkill:
    user_skill = UserSkill(user_id=user_id, **data)
    db.add(user_skill)
    db.commit()
    db.refresh(user_skill)
    return user_skill


def update_user_skill(db: Session, user_skill: UserSkill, changes: dict) -> UserSkill:
    for field, value in changes.items():
        setattr(user_skill, field, value)
    db.commit()
    db.refresh(user_skill)
    return user_skill


def delete_user_skill(db: Session, user_skill: UserSkill) -> None:
    db.delete(user_skill)
    db.commit()
