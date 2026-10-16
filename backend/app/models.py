"""SQLAlchemy models (database tables) for Mentora AI.

Status/proficiency fields are plain strings with sensible defaults, so they
are easy to read and change without database enum migrations.
"""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Core tables
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Deleting a user deletes everything that belongs to them
    learning_goals: Mapped[list["LearningGoal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    user_skills: Mapped[list["UserSkill"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    career_goals: Mapped[list["CareerGoal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class Skill(Base):
    """A skill in the shared catalog, e.g. "Python" or "SQL"."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100))

    user_skills: Mapped[list["UserSkill"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan", passive_deletes=True
    )


class LearningGoal(Base):
    __tablename__ = "learning_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    target_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="learning_goals")
    progress_entries: Mapped[list["LearningProgress"]] = relationship(
        back_populates="learning_goal",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LearningProgress.created_at",
    )

    # The latest progress update (progress_entries is ordered oldest first).
    # Completed goals count as 100% even without a final update.
    @property
    def latest_progress(self) -> "LearningProgress | None":
        return self.progress_entries[-1] if self.progress_entries else None

    @property
    def progress_percent(self) -> int:
        if self.status == "completed":
            return 100
        return self.latest_progress.progress_percent if self.latest_progress else 0

    @property
    def last_progress_at(self) -> datetime | None:
        return self.latest_progress.created_at if self.latest_progress else None


# ---------------------------------------------------------------------------
# Tracking tables
# ---------------------------------------------------------------------------


class UserSkill(Base):
    """Links a user to a skill, with how well they know it."""

    __tablename__ = "user_skills"
    # A user can have each skill only once
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skills_user_id_skill_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), index=True
    )
    proficiency: Mapped[str] = mapped_column(String(20), default="beginner")
    status: Mapped[str] = mapped_column(String(20), default="learning")

    user: Mapped["User"] = relationship(back_populates="user_skills")
    skill: Mapped["Skill"] = relationship(back_populates="user_skills")


class LearningProgress(Base):
    """One progress update (a snapshot) for a learning goal."""

    __tablename__ = "learning_progress"
    __table_args__ = (
        CheckConstraint(
            "progress_percent BETWEEN 0 AND 100",
            name="ck_learning_progress_percent_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learning_goal_id: Mapped[int] = mapped_column(
        ForeignKey("learning_goals.id", ondelete="CASCADE"), index=True
    )
    progress_percent: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    learning_goal: Mapped["LearningGoal"] = relationship(
        back_populates="progress_entries"
    )


class CareerGoal(Base):
    __tablename__ = "career_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    target_role: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    # Comma-separated list, e.g. "Python, SQL, Docker"
    required_skills: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    target_date: Mapped[date | None] = mapped_column(Date)

    user: Mapped["User"] = relationship(back_populates="career_goals")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    # Comma-separated list, e.g. "React, FastAPI, PostgreSQL"
    technologies: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="planned")
    # The write-up from the rich editor (HTML; images point to /api/uploads/<id>)
    content: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="projects")


# ---------------------------------------------------------------------------
# Uploaded files (chat attachments and project images)
# ---------------------------------------------------------------------------


class Upload(Base):
    """A file a user uploaded. The bytes live on disk (settings.UPLOAD_DIR)."""

    __tablename__ = "uploads"

    # Random id, so file URLs can't be guessed by counting
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))  # the original name, for display
    content_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    @property
    def url(self) -> str:
        return f"/api/uploads/{self.id}"
