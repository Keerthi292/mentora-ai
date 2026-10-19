"""Database access for logins (sessions). No HTTP or business rules here, only queries."""

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import LoginSession


def create_session(db: Session, session_id: str, user_id: int, expires_at: datetime) -> LoginSession:
    session = LoginSession(id=session_id, user_id=user_id, expires_at=expires_at)
    db.add(session)
    db.commit()
    return session


def get_valid_session(db: Session, session_id: str) -> LoginSession | None:
    stmt = select(LoginSession).where(
        LoginSession.id == session_id, LoginSession.expires_at > datetime.now(timezone.utc)
    )
    return db.scalars(stmt).first()


def delete_session(db: Session, session_id: str) -> None:
    db.execute(delete(LoginSession).where(LoginSession.id == session_id))
    db.commit()


def delete_expired_sessions(db: Session, user_id: int) -> None:
    db.execute(
        delete(LoginSession).where(
            LoginSession.user_id == user_id, LoginSession.expires_at <= datetime.now(timezone.utc)
        )
    )
    db.commit()
