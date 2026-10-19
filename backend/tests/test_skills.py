"""Tests for the /api/skills CRUD endpoints. Skills belong to the logged-in user."""

import pytest

from app.models import Skill

pytestmark = pytest.mark.usefixtures("demo_user")


def create_skill(client, name="Python", category="Programming"):
    response = client.post("/api/skills", json={"name": name, "category": category})
    assert response.status_code == 201
    return response.json()


# ---- Create ---------------------------------------------------------------


def test_create_skill(client):
    response = client.post("/api/skills", json={"name": "Python", "category": "Programming"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Python"
    assert body["category"] == "Programming"
    assert isinstance(body["id"], int)


def test_create_skill_strips_whitespace(client):
    assert create_skill(client, name="  SQL  ")["name"] == "SQL"


@pytest.mark.parametrize("duplicate", ["Python", "python", "  PYTHON "])
def test_create_duplicate_skill_returns_409(client, duplicate):
    create_skill(client, name="Python")

    response = client.post("/api/skills", json={"name": duplicate})
    assert response.status_code == 409


@pytest.mark.parametrize("payload", [{}, {"name": ""}, {"name": "   "}, {"name": "x" * 101}])
def test_create_skill_invalid_returns_422(client, payload):
    assert client.post("/api/skills", json=payload).status_code == 422


# ---- Read -----------------------------------------------------------------


def test_list_skills_sorted_by_name(client):
    create_skill(client, name="SQL")
    create_skill(client, name="Docker")

    response = client.get("/api/skills")

    assert response.status_code == 200
    assert [s["name"] for s in response.json()] == ["Docker", "SQL"]


def test_list_skills_pagination(client):
    for name in ["A", "B", "C"]:
        create_skill(client, name=name)

    response = client.get("/api/skills", params={"skip": 1, "limit": 1})
    assert [s["name"] for s in response.json()] == ["B"]


def test_get_skill(client):
    skill = create_skill(client)

    response = client.get(f"/api/skills/{skill['id']}")

    assert response.status_code == 200
    assert response.json() == skill


def test_get_missing_skill_returns_404(client):
    assert client.get("/api/skills/999999").status_code == 404


# ---- Update ---------------------------------------------------------------


def test_update_skill_only_changes_sent_fields(client):
    skill = create_skill(client, name="Python", category="Programming")

    response = client.patch(f"/api/skills/{skill['id']}", json={"category": "Language"})

    assert response.status_code == 200
    assert response.json() == {**skill, "category": "Language"}


def test_update_skill_to_existing_name_returns_409(client):
    create_skill(client, name="SQL")
    skill = create_skill(client, name="Python")

    response = client.patch(f"/api/skills/{skill['id']}", json={"name": "sql"})
    assert response.status_code == 409


def test_update_skill_keeping_own_name_is_allowed(client):
    skill = create_skill(client, name="Python")

    response = client.patch(f"/api/skills/{skill['id']}", json={"name": "Python"})
    assert response.status_code == 200


def test_update_skill_name_null_returns_422(client):
    skill = create_skill(client)
    assert client.patch(f"/api/skills/{skill['id']}", json={"name": None}).status_code == 422


def test_update_missing_skill_returns_404(client):
    assert client.patch("/api/skills/999999", json={"category": "x"}).status_code == 404


# ---- Delete ---------------------------------------------------------------


def test_delete_skill(client):
    skill = create_skill(client)

    response = client.delete(f"/api/skills/{skill['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/skills/{skill['id']}").status_code == 404


def test_delete_missing_skill_returns_404(client):
    assert client.delete("/api/skills/999999").status_code == 404


# ---- Each user has their own skills -------------------------------------------


def test_other_users_skills_are_hidden_and_protected(client, db, make_user):
    theirs = Skill(user_id=make_user().id, name="Rust")
    db.add(theirs)
    db.commit()

    assert client.get("/api/skills").json() == []
    assert client.get(f"/api/skills/{theirs.id}").status_code == 404
    assert client.patch(f"/api/skills/{theirs.id}", json={"name": "Mine"}).status_code == 404
    assert client.delete(f"/api/skills/{theirs.id}").status_code == 404
    # The same name is fine for a different user
    assert client.post("/api/skills", json={"name": "Rust"}).status_code == 201
    assert db.get(Skill, theirs.id).name == "Rust"


def test_cannot_set_a_level_on_another_users_skill(client, db, make_user):
    theirs = Skill(user_id=make_user().id, name="Go")
    db.add(theirs)
    db.commit()

    response = client.post("/api/user-skills", json={"skill_id": theirs.id})

    assert response.status_code == 404
