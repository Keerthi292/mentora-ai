"""Database access for projects. No HTTP or business rules here, only queries."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Project


def list_projects(
    db: Session, user_id: int, status: str | None = None, skip: int = 0, limit: int = 100
) -> list[Project]:
    stmt = select(Project).where(Project.user_id == user_id)
    if status is not None:
        stmt = stmt.where(Project.status == status)
    stmt = stmt.order_by(Project.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def get_project(db: Session, project_id: int, user_id: int) -> Project | None:
    # Filter by user_id too, so users can only see their own projects
    stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
    return db.scalars(stmt).first()


def lowercase_names(db: Session, user_id: int) -> set[str]:
    """The user's project names, lowercased (for quick "already saved?" checks)."""
    return set(db.scalars(select(func.lower(Project.name)).where(Project.user_id == user_id)))


def create_project(db: Session, user_id: int, data: dict) -> Project:
    project = Project(user_id=user_id, **data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project: Project, changes: dict) -> Project:
    for field, value in changes.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()
