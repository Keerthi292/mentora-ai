"""Business rules for accounts and logins: sign up, log in, log out, forgot password."""

import hmac
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.repositories import password_reset_repository, session_repository, user_repository
from app.schemas import LoginRequest, RegisterRequest, ResetPasswordRequest
from app.security import hash_password, new_reset_code, new_session_token, token_hash, verify_password


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
    """Make a 6-digit code for the account with this email. Returns (to, subject, text) for
    the email, or None if there's no such account (the caller answers the same either way)."""
    user = user_repository.get_user_by_email(db, email)
    if user is None:
        return None
    code = new_reset_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_CODE_MINUTES)
    password_reset_repository.replace_reset(db, user.id, token_hash(code), expires_at)

    text = (
        f"Hi {user.full_name},\n\n"
        "Someone (hopefully you) asked to reset your Mentora AI password. Enter this code in the app:\n\n"
        f"    {code}\n\n"
        f"It works once, for {settings.RESET_CODE_MINUTES} minutes. "
        "If you didn't ask for this, ignore this email: your password stays the same.\n"
    )
    return user.email, f"{code} is your Mentora AI reset code", text


def _wrong_code() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="That code is wrong or has expired. Check the email, or send a new code.",
    )


def reset_password(db: Session, payload: ResetPasswordRequest) -> User:
    """Set a new password with the emailed code. Every other login of the account ends.
    A wrong email, wrong code and expired code all get the same answer."""
    user = user_repository.get_user_by_email(db, payload.email)
    reset = password_reset_repository.get_reset(db, user.id) if user else None
    if reset is None:
        raise _wrong_code()
    if reset.expires_at <= datetime.now(timezone.utc):
        password_reset_repository.delete_reset(db, reset)
        raise _wrong_code()
    if not hmac.compare_digest(reset.code_hash, token_hash(payload.code.strip())):
        password_reset_repository.count_wrong_try(db, reset, settings.RESET_CODE_ATTEMPTS)
        raise _wrong_code()

    password_reset_repository.delete_reset_and_sessions(db, user.id)
    return user_repository.update_user(db, user, {"password_hash": hash_password(payload.password)})
