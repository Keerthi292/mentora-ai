"""Business rules for accounts and logins: sign up, log in, log out, forgot password."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.repositories import password_reset_repository, session_repository, user_repository
from app.schemas import LoginRequest, RegisterRequest, ResetPasswordRequest
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


def request_password_reset(db: Session, email: str) -> tuple[str, str, str] | None:
    """Make a reset link for the account with this email. Returns (to, subject, text) for
    the email, or None if there's no such account (the caller answers the same either way)."""
    user = user_repository.get_user_by_email(db, email)
    if user is None:
        return None
    token = new_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_TOKEN_MINUTES)
    password_reset_repository.replace_reset(db, token_hash(token), user.id, expires_at)

    link = f"{settings.APP_URL.rstrip('/')}/reset-password?token={token}"
    text = (
        f"Hi {user.full_name},\n\n"
        "Someone (hopefully you) asked to reset your Mentora AI password. Open this link to choose a new one:\n\n"
        f"{link}\n\n"
        f"It works once, for {settings.RESET_TOKEN_MINUTES} minutes. "
        "If you didn't ask for this, ignore this email: your password stays the same.\n"
    )
    return user.email, "Reset your Mentora AI password", text


def reset_password(db: Session, payload: ResetPasswordRequest) -> User:
    """Set a new password with a reset link's token. Every other login of the account ends."""
    reset = password_reset_repository.get_valid_reset(db, token_hash(payload.token))
    if reset is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired. Ask for a new one.",
        )
    user = user_repository.get_user(db, reset.user_id)
    password_reset_repository.delete_resets_and_sessions(db, user.id)
    return user_repository.update_user(db, user, {"password_hash": hash_password(payload.password)})
