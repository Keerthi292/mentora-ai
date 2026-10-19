from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.ai.agent import attachment_ids, get_daily_tip, get_mentor_response, stream_mentor_response
from app.ai.attachments import Attachment, load_attachments
from app.ai.context import build_user_profile
from app.ai.llm_client import LLMError
from app.ai.schemas import ChatRequest, ChatResponse, TipResponse
from app.database import get_db
from app.dependencies import get_current_user_id
from app.repositories import user_repository

router = APIRouter(prefix="/api/ai", tags=["AI Mentor"])


def _load_files(db: Session, user_id: int, request: ChatRequest) -> dict[str, Attachment]:
    """The files the model will see. 400 if a file attached to this message doesn't exist
    (files in older messages that are gone are just mentioned as unavailable)."""
    files = load_attachments(db, user_id, attachment_ids(request))
    if any(file_id not in files for file_id in request.attachments):
        raise HTTPException(status_code=400, detail="An attached file was not found. Please attach it again.")
    return files


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ChatResponse:
    profile = build_user_profile(db, user_id)
    files = _load_files(db, user_id, request)
    try:
        return get_mentor_response(request, profile, files)
    except LLMError as exc:
        # e.g. 503 not configured, 429 rate limited, 502/503/504 Gemini failed
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/tip", response_model=TipResponse)
def daily_tip(
    refresh: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> TipResponse:
    """A short personal tip from the mentor, based on the user's profile.

    Saved for the day, so Gemini is asked once a day; `?refresh=true` asks for a new one.
    """
    user = user_repository.get_user(db, user_id)
    today = date.today()
    if user and user.daily_tip and user.daily_tip_date == today and not refresh:
        return TipResponse(tip=user.daily_tip)

    profile = build_user_profile(db, user_id)
    try:
        tip = get_daily_tip(profile)
    except LLMError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if user:
        user_repository.update_user(db, user, {"daily_tip": tip.tip, "daily_tip_date": today})
    return tip


# A plain `def` so the database read runs in a worker thread; the reply itself
# still streams asynchronously.
@router.post("/chat/stream")
def chat_stream(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    profile = build_user_profile(db, user_id)
    files = _load_files(db, user_id, request)
    return StreamingResponse(
        stream_mentor_response(request, profile, files),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # stops proxies like nginx from buffering
        },
    )
