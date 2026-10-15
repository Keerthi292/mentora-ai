"""Business rules for projects: user/project existence and ownership checks."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Project
from app.repositories import project_repository
from app.schemas import ProjectCreate, ProjectUpdate
from app.services import user_service


def list_projects(
    db: Session, user_id: int, project_status: str | None, skip: int, limit: int
) -> list[Project]:
    user_service.ensure_user_exists(db, user_id)
    return project_repository.list_projects(db, user_id, project_status, skip, limit)


def get_project(db: Session, project_id: int, user_id: int) -> Project:
    # Another user's project is reported as "not found" on purpose
    project = project_repository.get_project(db, project_id, user_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def create_project(db: Session, user_id: int, payload: ProjectCreate) -> Project:
    user_service.ensure_user_exists(db, user_id)
    return project_repository.create_project(db, user_id, payload.model_dump())


def update_project(
    db: Session, project_id: int, user_id: int, payload: ProjectUpdate
) -> Project:
    project = get_project(db, project_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    return project_repository.update_project(db, project, changes)


def delete_project(db: Session, project_id: int, user_id: int) -> None:
    project = get_project(db, project_id, user_id)
    project_repository.delete_project(db, project)
