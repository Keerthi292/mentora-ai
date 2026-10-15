from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SkillCreate, SkillResponse, SkillUpdate
from app.services import skill_service

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.get("", response_model=list[SkillResponse])
def list_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return skill_service.list_skills(db, skip, limit)


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(payload: SkillCreate, db: Session = Depends(get_db)):
    return skill_service.create_skill(db, payload)


@router.get("/{skill_id}", response_model=SkillResponse)
def get_skill(skill_id: int, db: Session = Depends(get_db)):
    return skill_service.get_skill(db, skill_id)


@router.patch("/{skill_id}", response_model=SkillResponse)
def update_skill(skill_id: int, payload: SkillUpdate, db: Session = Depends(get_db)):
    return skill_service.update_skill(db, skill_id, payload)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: int, db: Session = Depends(get_db)) -> None:
    skill_service.delete_skill(db, skill_id)
