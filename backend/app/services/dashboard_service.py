"""Builds the dashboard summary: counts per page and learning-goal progress."""

from datetime import date

from sqlalchemy.orm import Session

from app.models import CareerGoal, LearningGoal, Project
from app.repositories import dashboard_repository
from app.schemas import DashboardCounts, DashboardGoal, DashboardResponse
from app.services import user_service

MAX_GOALS = 20

# Active goals first, then paused, then completed; within each, the nearest target date first
_STATUS_ORDER = {"active": 0, "paused": 1, "completed": 2}


def get_dashboard(db: Session, user_id: int) -> DashboardResponse:
    user_service.ensure_user_exists(db, user_id)

    goal_statuses = dashboard_repository.count_by_status(db, LearningGoal, user_id)
    career_statuses = dashboard_repository.count_by_status(db, CareerGoal, user_id)
    project_statuses = dashboard_repository.count_by_status(db, Project, user_id)

    counts = DashboardCounts(
        skills=dashboard_repository.count_skills(db, user_id),
        learning_goals=sum(goal_statuses.values()),
        active_learning_goals=goal_statuses.get("active", 0),
        career_goals=sum(career_statuses.values()),
        active_career_goals=career_statuses.get("active", 0),
        projects=sum(project_statuses.values()),
        projects_in_progress=project_statuses.get("in_progress", 0),
    )

    goals = []
    for goal in dashboard_repository.list_goals_with_progress(db, user_id, MAX_GOALS):
        goals.append(
            DashboardGoal(
                id=goal.id,
                title=goal.title,
                status=goal.status,
                target_date=goal.target_date,
                progress_percent=goal.progress_percent,  # see LearningGoal in models.py
                last_update=goal.last_progress_at,
            )
        )
    goals.sort(key=lambda g: (_STATUS_ORDER.get(g.status, 3), g.target_date or date.max))

    return DashboardResponse(counts=counts, goals=goals)
