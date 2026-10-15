"""Pydantic schemas: the shapes of API request bodies and responses.

Each resource has three schemas:
- Create:   body for POST (required fields are required)
- Update:   body for PATCH (every field optional; only sent fields change)
- Response: what the API returns (built from a SQLAlchemy object)
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Allowed values for each status/level field. Anything else gets a 422 error.
LearningGoalStatus = Literal["active", "paused", "completed", "abandoned"]
Proficiency = Literal["beginner", "intermediate", "advanced", "expert"]
UserSkillStatus = Literal["want_to_learn", "learning", "acquired"]
CareerGoalStatus = Literal["active", "paused", "achieved", "abandoned"]
ProjectStatus = Literal["planned", "in_progress", "completed", "on_hold"]


class InputSchema(BaseModel):
    # Trim spaces so " Python " and "Python" are treated the same
    model_config = ConfigDict(str_strip_whitespace=True)


# Note on Update schemas: `name: str = Field(default=None)` means the field can
# be left out, but if it IS sent it must be a real string. So `{"name": null}`
# is rejected (422) instead of crashing on a NOT NULL database column.
# Fields that are nullable in the database use `str | None` so they can be cleared.


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


class SkillCreate(InputSchema):
    name: str = Field(min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)


class SkillUpdate(InputSchema):
    name: str = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str | None


# ---------------------------------------------------------------------------
# Learning goals
# ---------------------------------------------------------------------------


class LearningGoalCreate(InputSchema):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: LearningGoalStatus = "active"
    target_date: date | None = None


class LearningGoalUpdate(InputSchema):
    title: str = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: LearningGoalStatus = None
    target_date: date | None = None


class LearningGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: str | None
    status: str
    target_date: date | None
    created_at: datetime


# ---------------------------------------------------------------------------
# User skills (a user's link to a skill from the catalog)
# ---------------------------------------------------------------------------


class UserSkillCreate(InputSchema):
    skill_id: int = Field(ge=1)
    proficiency: Proficiency = "beginner"
    status: UserSkillStatus = "learning"


class UserSkillUpdate(InputSchema):
    # skill_id can't be changed: delete the entry and add the other skill instead
    proficiency: Proficiency = None
    status: UserSkillStatus = None


class UserSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    skill_id: int
    proficiency: str
    status: str
    # The skill's details, so the frontend doesn't need a second request
    skill: SkillResponse


# ---------------------------------------------------------------------------
# Learning progress (progress updates for one learning goal)
# ---------------------------------------------------------------------------


class LearningProgressCreate(InputSchema):
    progress_percent: int = Field(ge=0, le=100)
    note: str | None = None


class LearningProgressUpdate(InputSchema):
    progress_percent: int = Field(default=None, ge=0, le=100)
    note: str | None = None


class LearningProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    learning_goal_id: int
    progress_percent: int
    note: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Career goals
# ---------------------------------------------------------------------------


class CareerGoalCreate(InputSchema):
    target_role: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: CareerGoalStatus = "active"
    target_date: date | None = None


class CareerGoalUpdate(InputSchema):
    target_role: str = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: CareerGoalStatus = None
    target_date: date | None = None


class CareerGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    target_role: str
    description: str | None
    status: str
    target_date: date | None


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class ProjectCreate(InputSchema):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    technologies: str | None = Field(default=None, examples=["React, FastAPI, PostgreSQL"])
    status: ProjectStatus = "planned"


class ProjectUpdate(InputSchema):
    name: str = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    technologies: str | None = None
    status: ProjectStatus = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: str | None
    technologies: str | None
    status: str
