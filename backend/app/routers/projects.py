from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas import ProjectCreate, ProjectResponse, ProjectStatus, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    user_id: int = Depends(get_current_user_id),
    project_status: ProjectStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return project_service.list_projects(db, user_id, project_status, skip, limit)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return project_service.create_project(db, user_id, payload)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return project_service.get_project(db, project_id, user_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return project_service.update_project(db, project_id, user_id, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    project_service.delete_project(db, project_id, user_id)
