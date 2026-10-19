"""Shared FastAPI dependencies."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import session_repository
from app.security import token_hash

SESSION_COOKIE = "mentora_session"


def get_current_user_id(request: Request, db: Session = Depends(get_db)) -> int:
    """The id of the logged-in user, from the session cookie. 401 if not logged in."""
    token = request.cookies.get(SESSION_COOKIE)
    session = session_repository.get_valid_session(db, token_hash(token)) if token else None
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in.")
    return session.user_id
