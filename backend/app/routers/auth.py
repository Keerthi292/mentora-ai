from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import SESSION_COOKIE
from app.mailer import send_email
from app.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    # httpOnly: JavaScript can't read it (safe from XSS); SameSite=Lax: not sent by other sites' forms
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.SESSION_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    """Create an account and log in."""
    user = auth_service.register(db, payload)
    _set_session_cookie(response, auth_service.start_session(db, user.id))
    return user


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, payload)
    _set_session_cookie(response, auth_service.start_session(db, user.id))
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    """End this login (the session is deleted, not just the cookie)."""
    auth_service.end_session(db, request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(payload: ForgotPasswordRequest, background: BackgroundTasks, db: Session = Depends(get_db)):
    """Email a 6-digit reset code. The same answer whether or not the email has an account, and
    the email is sent after the response, so neither the answer nor its timing reveals which do."""
    email = auth_service.request_password_reset(db, payload.email)
    if email:
        background.add_task(send_email, *email)
    return {"detail": "If an account uses this email, a code is on its way."}


@router.post("/reset-password", response_model=UserResponse)
def reset_password(payload: ResetPasswordRequest, response: Response, db: Session = Depends(get_db)):
    """Choose a new password with the emailed code, then log in."""
    user = auth_service.reset_password(db, payload)
    _set_session_cookie(response, auth_service.start_session(db, user.id))
    return user
