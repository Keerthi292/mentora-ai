"""Business rules for mentor chats: ownership, and saving a whole chat at once.

The chat page streams replies straight from /api/ai/chat/stream, then saves the
conversation here (PUT) once the reply is finished. Saving replaces every
message, so editing a message (which drops the replies after it) is simple.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Conversation
from app.repositories import conversation_repository
from app.schemas import (
    ConversationDetail,
    ConversationRename,
    ConversationSave,
    StoredChatMessage,
)
from app.services import user_service


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")


def _own_conversation(db: Session, conversation_id: str, user_id: int) -> Conversation | None:
    """The user's conversation, None if it doesn't exist yet. Another user's is a 404."""
    conversation = conversation_repository.get_conversation(db, conversation_id)
    if conversation is not None and conversation.user_id != user_id:
        raise _not_found()
    return conversation


def list_conversations(db: Session, user_id: int) -> list[Conversation]:
    user_service.ensure_user_exists(db, user_id)
    return conversation_repository.list_conversations(db, user_id)


def get_conversation(db: Session, conversation_id: str, user_id: int) -> ConversationDetail:
    conversation = _own_conversation(db, conversation_id, user_id)
    if conversation is None:
        raise _not_found()
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            StoredChatMessage(
                id=m.client_id,
                role=m.role,
                content=m.content,
                attachments=m.attachments,
                error=m.error,
                stopped=m.stopped,
                edited=m.edited,
            )
            for m in conversation.messages
        ],
    )


def save_conversation(db: Session, conversation_id: str, user_id: int, payload: ConversationSave) -> Conversation:
    """Create the chat, or replace its title and messages."""
    user_service.ensure_user_exists(db, user_id)
    conversation = _own_conversation(db, conversation_id, user_id)
    if conversation is None:
        conversation = Conversation(id=conversation_id, user_id=user_id)

    messages = [
        {
            "client_id": m.id,
            "role": m.role,
            "content": m.content,
            "attachments": [a.model_dump() for a in m.attachments],
            "error": m.error,
            "stopped": m.stopped,
            "edited": m.edited,
        }
        for m in payload.messages
    ]
    changes = {"title": payload.title, "updated_at": payload.updated_at or datetime.now(timezone.utc)}
    try:
        return conversation_repository.save_conversation(db, conversation, changes, messages)
    except IntegrityError:
        # The same new chat was saved twice at the same moment; the other save won
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This chat was just saved. Please try again.")


def rename_conversation(
    db: Session, conversation_id: str, user_id: int, payload: ConversationRename
) -> Conversation:
    conversation = _own_conversation(db, conversation_id, user_id)
    if conversation is None:
        raise _not_found()
    return conversation_repository.save_conversation(db, conversation, {"title": payload.title})


def delete_conversation(db: Session, conversation_id: str, user_id: int) -> None:
    conversation = _own_conversation(db, conversation_id, user_id)
    if conversation is None:
        raise _not_found()
    conversation_repository.delete_conversation(db, conversation)
