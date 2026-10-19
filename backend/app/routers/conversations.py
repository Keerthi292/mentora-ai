from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas import ConversationDetail, ConversationRename, ConversationSave, ConversationSummary
from app.services import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["Mentor chats"])

# Chat ids are made by the browser (UUIDs)
ConversationId = Path(pattern=r"^[A-Za-z0-9_-]{1,64}$")


@router.get("", response_model=list[ConversationSummary])
def list_conversations(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Your chats, newest first (without their messages)."""
    return conversation_service.list_conversations(db, user_id)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str = ConversationId,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return conversation_service.get_conversation(db, conversation_id, user_id)


@router.put("/{conversation_id}", response_model=ConversationSummary)
def save_conversation(
    payload: ConversationSave,
    conversation_id: str = ConversationId,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create the chat, or replace its title and all its messages."""
    return conversation_service.save_conversation(db, conversation_id, user_id, payload)


@router.patch("/{conversation_id}", response_model=ConversationSummary)
def rename_conversation(
    payload: ConversationRename,
    conversation_id: str = ConversationId,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return conversation_service.rename_conversation(db, conversation_id, user_id, payload)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str = ConversationId,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    conversation_service.delete_conversation(db, conversation_id, user_id)
