from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.llm_client import LLMError
from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas import ResumeImportRequest, ResumeImportResponse, ResumeParseRequest, ResumeParseResponse
from app.services import resume_service

router = APIRouter(prefix="/api/resume", tags=["Resume import"])


@router.post("/parse", response_model=ResumeParseResponse)
def parse_resume(
    request: ResumeParseRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ResumeParseResponse:
    """Read an uploaded resume and list the skills and projects in it. Saves nothing."""
    try:
        return resume_service.parse_resume(db, user_id, request.upload_id)
    except LLMError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/import", response_model=ResumeImportResponse)
def import_resume(
    payload: ResumeImportRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ResumeImportResponse:
    """Save the skills and projects the user kept. Ones already saved are skipped."""
    return resume_service.import_resume(db, user_id, payload)
