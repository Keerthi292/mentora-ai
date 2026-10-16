"""Builds the user's profile (skills, goals, projects) that the mentor sees.

The profile is plain text added to the system prompt, so Gemini can give advice
based on what the user saved on the other pages instead of asking for it.
"""

import html
import logging
import re
from datetime import date

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import LearningGoal, User
from app.repositories import (
    career_goal_repository,
    learning_goal_repository,
    project_repository,
    skill_repository,
    user_skill_repository,
)

logger = logging.getLogger(__name__)

# Keep the prompt small: at most this many items per section, and short descriptions
MAX_ITEMS = 20
MAX_TEXT = 300


def _short(text: str | None) -> str:
    text = " ".join((text or "").split())  # one line
    return text if len(text) <= MAX_TEXT else text[: MAX_TEXT - 1] + "…"


def _html_text(content: str | None) -> str:
    """Plain text of a project write-up (HTML from the editor)."""
    return html.unescape(re.sub(r"<[^>]+>", " ", content or ""))


def _section(title: str, lines: list[str]) -> str:
    body = "\n".join(f"- {line}" for line in lines) if lines else "(none yet)"
    return f"{title}:\n{body}"


def _details(*parts: str | None) -> str:
    return ", ".join(p for p in parts if p)


def _goal_line(goal: LearningGoal) -> str:
    latest = goal.progress_entries[-1] if goal.progress_entries else None
    progress = None
    if latest:
        progress = f"latest progress {latest.progress_percent}%"
        if latest.note:
            progress += f' ("{_short(latest.note)}")'
    target = f"target {goal.target_date.isoformat()}" if goal.target_date else None
    line = f"{goal.title} [{_details(goal.status, target, progress)}]"
    return f"{line}: {_short(goal.description)}" if goal.description else line


def build_user_profile(db: Session, user_id: int) -> str | None:
    """Return the user's profile as text, or None if the database can't be read."""
    try:
        user = db.get(User, user_id)
        skills = skill_repository.list_skills(db, limit=MAX_ITEMS)
        user_skills = user_skill_repository.list_user_skills(db, user_id, limit=MAX_ITEMS)
        goals = learning_goal_repository.list_goals(db, user_id, limit=MAX_ITEMS)
        career_goals = career_goal_repository.list_career_goals(db, user_id, limit=MAX_ITEMS)
        projects = project_repository.list_projects(db, user_id, limit=MAX_ITEMS)

        sections = [
            f"Name: {user.full_name if user else 'unknown'}\nToday: {date.today().isoformat()}",
            _section(
                "Skills (Skills page)",
                [f"{s.name} ({s.category})" if s.category else s.name for s in skills],
            ),
            _section(
                "Skill levels",
                [f"{us.skill.name}: {us.proficiency}, {us.status}" for us in user_skills],
            ),
            _section("Learning goals", [_goal_line(g) for g in goals]),
            _section(
                "Career goals",
                [
                    f"{c.target_role} [{_details(c.status, f'target {c.target_date.isoformat()}' if c.target_date else None, f'skills needed: {c.required_skills}' if c.required_skills else None)}]"
                    + (f": {_short(c.description)}" if c.description else "")
                    for c in career_goals
                ],
            ),
            _section(
                "Projects",
                [
                    f"{p.name} [{_details(p.status, f'tech: {p.technologies}' if p.technologies else None)}]"
                    + (f": {_short(p.description or _html_text(p.content))}" if p.description or p.content else "")
                    for p in projects
                ],
            ),
        ]
        return "\n\n".join(sections)
    except SQLAlchemyError:
        # The mentor still answers, just without personal context
        logger.exception("Could not load the user's profile for the mentor")
        return None
