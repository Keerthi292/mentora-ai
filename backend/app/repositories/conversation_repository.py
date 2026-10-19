"""Database access for mentor chats. No HTTP or business rules here, only queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ChatMessage, Conversation


def list_conversations(db: Session, user_id: int, limit: int = 200) -> list[Conversation]:
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def get_conversation(db: Session, conversation_id: str) -> Conversation | None:
    """Any user's conversation (the service checks the owner)."""
    stmt = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    return db.scalars(stmt).first()


def save_conversation(
    db: Session, conversation: Conversation, changes: dict, messages: list[dict] | None = None
) -> Conversation:
    """Apply `changes`; if `messages` is given, it replaces all of the chat's messages."""
    for field, value in changes.items():
        setattr(conversation, field, value)
    if messages is not None:
        conversation.messages.clear()
        # Remove the old rows before adding new ones at the same positions
        db.flush()
        conversation.messages.extend(ChatMessage(position=i, **m) for i, m in enumerate(messages))
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def delete_conversation(db: Session, conversation: Conversation) -> None:
    db.delete(conversation)
    db.commit()
