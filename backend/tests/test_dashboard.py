"""Tests for GET /api/dashboard (counts and learning-goal progress)."""

from datetime import date

import pytest

from app.models import CareerGoal, LearningGoal, LearningProgress, Project, Skill

URL = "/api/dashboard"

pytestmark = pytest.mark.usefixtures("demo_user")


def test_empty_dashboard(client):
    response = client.get(URL)

    assert response.status_code == 200
    body = response.json()
    assert body["goals"] == []
    assert all(value == 0 for value in body["counts"].values())


def test_counts(client, db, demo_user, make_user):
    db.add_all([Skill(user_id=1, name="Python"), Skill(user_id=1, name="SQL")])
    db.add_all(
        [
            LearningGoal(user_id=demo_user.id, title="A", status="active"),
            LearningGoal(user_id=demo_user.id, title="B", status="paused"),
            CareerGoal(user_id=demo_user.id, target_role="Backend Engineer", status="active"),
            CareerGoal(user_id=demo_user.id, target_role="Old role", status="abandoned"),
            Project(user_id=demo_user.id, name="P1", status="in_progress"),
            Project(user_id=demo_user.id, name="P2", status="planned"),
        ]
    )
    other = make_user()
    db.add(LearningGoal(user_id=other.id, title="Not mine", status="active"))
    db.commit()

    counts = client.get(URL).json()["counts"]

    assert counts == {
        "skills": 2,
        "learning_goals": 2,
        "active_learning_goals": 1,
        "career_goals": 2,
        "active_career_goals": 1,
        "projects": 2,
        "projects_in_progress": 1,
    }


def test_goals_show_latest_progress_and_are_ordered(client, db, demo_user, make_user):
    later = LearningGoal(user_id=demo_user.id, title="Later", status="active", target_date=date(2027, 6, 1))
    sooner = LearningGoal(user_id=demo_user.id, title="Sooner", status="active", target_date=date(2026, 12, 1))
    done = LearningGoal(user_id=demo_user.id, title="Done", status="completed")
    dropped = LearningGoal(user_id=demo_user.id, title="Dropped", status="abandoned")
    db.add_all([later, sooner, done, dropped])
    db.flush()
    db.add_all(
        [
            LearningProgress(learning_goal_id=sooner.id, progress_percent=20),
            LearningProgress(learning_goal_id=sooner.id, progress_percent=55),
        ]
    )
    other = make_user()
    db.add(LearningGoal(user_id=other.id, title="Not mine"))
    db.commit()

    goals = client.get(URL).json()["goals"]

    assert [g["title"] for g in goals] == ["Sooner", "Later", "Done"]  # abandoned hidden
    assert goals[0]["progress_percent"] == 55  # the latest update
    assert goals[0]["last_update"] is not None
    assert goals[1]["progress_percent"] == 0  # no updates yet
    assert goals[1]["last_update"] is None
    assert goals[2]["progress_percent"] == 100  # completed counts as 100%
