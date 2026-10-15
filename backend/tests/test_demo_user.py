"""Tests for the demo user setup (app/seed.py and app/dependencies.py)."""

from app.config import settings
from app.dependencies import get_current_user_id
from app.models import User
from app.seed import DEMO_USER_EMAIL, DEMO_USER_NAME, seed_demo_user


def test_get_current_user_id_returns_demo_user_id():
    assert get_current_user_id() == settings.DEMO_USER_ID


def test_seed_creates_demo_user(db):
    assert seed_demo_user(db) is True

    user = db.get(User, settings.DEMO_USER_ID)
    assert user.full_name == DEMO_USER_NAME
    assert user.email == DEMO_USER_EMAIL


def test_seed_is_safe_to_run_twice(db):
    assert seed_demo_user(db) is True
    assert seed_demo_user(db) is False

    assert db.query(User).count() == 1


def test_new_users_after_seed_get_a_different_id(db, make_user):
    # The seed inserts id=1 itself, so it must move the id counter forward,
    # otherwise this insert would crash with a duplicate id
    seed_demo_user(db)

    other = make_user("Other User")

    assert other.id != settings.DEMO_USER_ID


def test_endpoints_return_404_when_demo_user_is_missing(client):
    # No seed here: the API should say clearly that the user doesn't exist
    response = client.get("/api/learning-goals")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
