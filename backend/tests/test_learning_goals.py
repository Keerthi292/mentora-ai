"""Tests for the /api/learning-goals CRUD endpoints.

There is no login yet: every request acts as the demo user (see app/dependencies.py).
"""

import pytest

from app.models import LearningGoal

URL = "/api/learning-goals"

# Every test in this file needs the demo user to exist
pytestmark = pytest.mark.usefixtures("demo_user")


def create_goal(client, **fields):
    payload = {"title": "Learn FastAPI", **fields}
    response = client.post(URL, json=payload)
    assert response.status_code == 201
    return response.json()


def create_goal_for_other_user(db, make_user, title="Someone else's goal") -> LearningGoal:
    """Insert a goal owned by a different user directly in the database."""
    other = make_user("Other User")
    goal = LearningGoal(user_id=other.id, title=title)
    db.add(goal)
    db.commit()
    return goal


# ---- Create ---------------------------------------------------------------


def test_create_goal_with_defaults(client, demo_user):
    response = client.post(URL, json={"title": "Learn FastAPI"})

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == demo_user.id
    assert body["title"] == "Learn FastAPI"
    assert body["status"] == "active"
    assert body["description"] is None
    assert body["target_date"] is None
    assert body["created_at"]


def test_create_goal_with_all_fields(client):
    goal = create_goal(
        client, description="Build an API", status="paused", target_date="2026-12-31"
    )

    assert goal["description"] == "Build an API"
    assert goal["status"] == "paused"
    assert goal["target_date"] == "2026-12-31"


def test_create_goal_ignores_user_id_query_param(client, demo_user, make_user):
    # The old ?user_id= parameter must not let anyone write as another user
    other = make_user("Other User")

    response = client.post(URL, params={"user_id": other.id}, json={"title": "x"})

    assert response.json()["user_id"] == demo_user.id


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "x", "status": "done"},
        {"title": "x", "target_date": "someday"},
    ],
)
def test_create_goal_invalid_body_returns_422(client, payload):
    assert client.post(URL, json=payload).status_code == 422


# ---- Read -----------------------------------------------------------------


def test_list_goals_only_returns_demo_users_goals(client, db, make_user):
    create_goal(client, title="My goal")
    create_goal_for_other_user(db, make_user)

    response = client.get(URL)

    assert response.status_code == 200
    assert [g["title"] for g in response.json()] == ["My goal"]


def test_list_goals_filter_by_status(client):
    create_goal(client, title="Active one")
    create_goal(client, title="Paused one", status="paused")

    response = client.get(URL, params={"status": "paused"})

    assert [g["title"] for g in response.json()] == ["Paused one"]


def test_list_goals_invalid_status_filter_returns_422(client):
    assert client.get(URL, params={"status": "bogus"}).status_code == 422


def test_get_goal(client):
    goal = create_goal(client)

    response = client.get(f"{URL}/{goal['id']}")

    assert response.status_code == 200
    assert response.json() == goal


def test_get_other_users_goal_returns_404(client, db, make_user):
    other_goal = create_goal_for_other_user(db, make_user)
    assert client.get(f"{URL}/{other_goal.id}").status_code == 404


def test_get_missing_goal_returns_404(client):
    assert client.get(f"{URL}/999999").status_code == 404


# ---- Update ---------------------------------------------------------------


def test_update_goal_only_changes_sent_fields(client):
    goal = create_goal(client, description="Keep me")

    response = client.patch(f"{URL}/{goal['id']}", json={"status": "completed"})

    assert response.status_code == 200
    # A completed goal counts as 100% done
    assert response.json() == {**goal, "status": "completed", "progress_percent": 100}


def test_update_goal_can_clear_optional_field(client):
    goal = create_goal(client, target_date="2026-12-31")

    response = client.patch(f"{URL}/{goal['id']}", json={"target_date": None})

    assert response.json()["target_date"] is None


@pytest.mark.parametrize("payload", [{"status": "finished"}, {"title": None}, {"title": ""}])
def test_update_goal_invalid_body_returns_422(client, payload):
    goal = create_goal(client)
    assert client.patch(f"{URL}/{goal['id']}", json=payload).status_code == 422


def test_update_other_users_goal_returns_404(client, db, make_user):
    other_goal = create_goal_for_other_user(db, make_user, title="Untouched")

    response = client.patch(f"{URL}/{other_goal.id}", json={"title": "Hacked"})

    assert response.status_code == 404
    db.refresh(other_goal)
    assert other_goal.title == "Untouched"


# ---- Delete ---------------------------------------------------------------


def test_delete_goal(client):
    goal = create_goal(client)

    response = client.delete(f"{URL}/{goal['id']}")

    assert response.status_code == 204
    assert client.get(f"{URL}/{goal['id']}").status_code == 404


def test_delete_other_users_goal_returns_404(client, db, make_user):
    other_goal = create_goal_for_other_user(db, make_user)

    assert client.delete(f"{URL}/{other_goal.id}").status_code == 404
    assert db.get(LearningGoal, other_goal.id) is not None
