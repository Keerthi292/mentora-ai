"""Database engine, session factory, and the declarative Base for models."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# pool_pre_ping checks a connection is alive before using it
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """All models inherit from this class."""


def get_db():
    """FastAPI dependency: yields a session and always closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
