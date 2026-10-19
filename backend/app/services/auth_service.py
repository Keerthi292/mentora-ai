"""Business rules for accounts and logins: sign up, log in, log out."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.repositories import session_repository, user_repository
from app.schemas import LoginRequest, RegisterRequest
from app.security import hash_password, new_session_token, token_hash, verify_password


def _email_taken() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")


def register(db: Session, payload: RegisterRequest) -> User:
    if user_repository.get_user_by_email(db, payload.email):
        raise _email_taken()
    try:
        return user_repository.create_user(
            db,
            {"full_name": payload.full_name, "email": payload.email, "password_hash": hash_password(payload.password)},
        )
    except IntegrityError:
        db.rollback()
        raise _email_taken()


def authenticate(db: Session, payload: LoginRequest) -> User:
    """The user if the email and password match. The same 401 either way, so the
    response doesn't reveal which emails have an account."""
    user = user_repository.get_user_by_email(db, payload.email)
    # Checked even without an account, so both cases take the same time
    if not verify_password(payload.password, user.password_hash if user else None):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong email or password.")
    return user


def start_session(db: Session, user_id: int) -> str:
    """Create a login and return its token (for the cookie)."""
    session_repository.delete_expired_sessions(db, user_id)
    token = new_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.SESSION_DAYS)
    session_repository.create_session(db, token_hash(token), user_id, expires_at)
    return token


def end_session(db: Session, token: str | None) -> None:
    if token:
        session_repository.delete_session(db, token_hash(token))
