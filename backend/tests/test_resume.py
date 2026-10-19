"""Tests for /api/resume/parse and /api/resume/import.

Gemini is replaced by a fake client that answers with fixed JSON.
"""

import json

import pytest
from google.genai import errors, types

from app.ai import llm_client
from app.models import Project, Skill, Upload, UserSkill

pytestmark = pytest.mark.usefixtures("demo_user")

PDF = b"%PDF-1.7\n" + b"x" * 64

GEMINI_ANSWER = {
    "skills": [
        {"name": " Python ", "category": "Programming", "proficiency": "Advanced"},
        {"name": "python", "category": "Programming", "proficiency": "beginner"},  # duplicate
        {"name": "React", "category": "Frontend", "proficiency": "guru"},  # unknown level
        {"name": "   ", "category": "", "proficiency": "expert"},  # empty name
    ],
    "projects": [
        {
            "name": "Mentora AI",
            "description": "An AI career mentor.",
            "technologies": ["FastAPI", "React", "FastAPI"],
            "highlights": ["Built streaming chat", "Wrote 130 tests <b>"],
        },
        {"name": "Weather App", "description": "", "technologies": [], "highlights": []},
    ],
}


class FakeGemini:
    def __init__(self):
        self.answer = json.dumps(GEMINI_ANSWER)
        self.error = None
        self.calls = []
        self.models = self

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return types.GenerateContentResponse(
            candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part(text=self.answer)]))]
        )


@pytest.fixture
def fake_gemini(monkeypatch):
    fake = FakeGemini()
    monkeypatch.setattr(llm_client, "_create_client", lambda *args, **kwargs: fake)
    return fake


def upload(client, name="resume.pdf", data=PDF) -> str:
    response = client.post("/api/uploads", files={"file": (name, data, "application/octet-stream")})
    assert response.status_code == 201
    return response.json()["id"]


# --- POST /api/resume/parse ---------------------------------------------------


def test_parse_returns_tidied_skills_and_projects(client, fake_gemini):
    response = client.post("/api/resume/parse", json={"upload_id": upload(client)})

    assert response.status_code == 200
    body = response.json()
    assert body["skills"] == [
        {"name": "Python", "category": "Programming", "proficiency": "advanced", "already_saved": False},
        {"name": "React", "category": "Frontend", "proficiency": "intermediate", "already_saved": False},
    ]
    assert [p["name"] for p in body["projects"]] == ["Mentora AI", "Weather App"]
    assert body["projects"][0]["technologies"] == ["FastAPI", "React"]
    assert body["projects"][1]["description"] is None


def test_parse_sends_the_pdf_to_gemini_in_json_mode(client, fake_gemini):
    client.post("/api/resume/parse", json={"upload_id": upload(client)})

    call = fake_gemini.calls[0]
    assert call["config"].response_mime_type == "application/json"
    parts = call["contents"][0].parts
    assert parts[1].inline_data.mime_type == "application/pdf"
    assert parts[1].inline_data.data == PDF


def test_parse_sends_a_text_resume_as_text(client, fake_gemini):
    upload_id = upload(client, "resume.md", b"# Jane\nSkills: Python")
    client.post("/api/resume/parse", json={"upload_id": upload_id})

    assert "Skills: Python" in fake_gemini.calls[0]["contents"][0].parts[1].text


def test_parse_marks_items_already_saved(client, fake_gemini, db, demo_user):
    db.add_all([Skill(name="python"), Project(user_id=demo_user.id, name="MENTORA AI")])
    db.commit()

    body = client.post("/api/resume/parse", json={"upload_id": upload(client)}).json()

    assert [s["already_saved"] for s in body["skills"]] == [True, False]
    assert [p["already_saved"] for p in body["projects"]] == [True, False]


def test_parse_saves_nothing(client, fake_gemini, db):
    client.post("/api/resume/parse", json={"upload_id": upload(client)})

    assert db.query(Skill).count() == 0
    assert db.query(Project).count() == 0


def test_parse_unknown_file_returns_404(client, fake_gemini):
    response = client.post("/api/resume/parse", json={"upload_id": "0" * 32})
    assert response.status_code == 404


def test_parse_another_users_file_returns_404(client, fake_gemini, db, make_user):
    upload_id = upload(client)
    db.get(Upload, upload_id).user_id = make_user().id
    db.commit()

    assert client.post("/api/resume/parse", json={"upload_id": upload_id}).status_code == 404


def test_parse_gif_is_rejected(client, fake_gemini):
    upload_id = upload(client, "resume.gif", b"GIF89a" + b"\x00" * 32)

    response = client.post("/api/resume/parse", json={"upload_id": upload_id})

    assert response.status_code == 400
    assert fake_gemini.calls == []


def test_parse_invalid_id_returns_422(client, fake_gemini):
    assert client.post("/api/resume/parse", json={"upload_id": "../etc/passwd"}).status_code == 422


def test_parse_gemini_rate_limit_returns_429(client, fake_gemini):
    fake_gemini.error = errors.ClientError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "quota"}})

    response = client.post("/api/resume/parse", json={"upload_id": upload(client)})

    assert response.status_code == 429


def test_parse_bad_json_from_gemini_returns_502(client, fake_gemini):
    fake_gemini.answer = '{"skills": "not a list"}'

    response = client.post("/api/resume/parse", json={"upload_id": upload(client)})

    assert response.status_code == 502
    assert "unexpected answer" in response.json()["detail"]


# --- POST /api/resume/import --------------------------------------------------

IMPORT = {
    "skills": [
        {"name": "Python", "category": "Programming", "proficiency": "advanced"},
        {"name": "React", "category": "Frontend", "proficiency": "beginner"},
    ],
    "projects": [
        {
            "name": "Mentora AI",
            "description": "An AI career mentor.",
            "technologies": ["FastAPI", "React"],
            "highlights": ["Built streaming chat", "Wrote <b>tests</b>"],
        }
    ],
}


def test_import_saves_skills_levels_and_projects(client, db, demo_user):
    response = client.post("/api/resume/import", json=IMPORT)

    assert response.status_code == 200
    assert response.json() == {"skills_added": 2, "skills_skipped": 0, "projects_added": 1, "projects_skipped": 0}

    levels = {us.skill.name: (us.proficiency, us.status) for us in db.query(UserSkill).all()}
    assert levels == {"Python": ("advanced", "acquired"), "React": ("beginner", "acquired")}

    project = db.query(Project).one()
    assert project.user_id == demo_user.id
    assert project.technologies == "FastAPI, React"
    assert project.status == "completed"
    # Bullet points become the write-up, with HTML escaped
    assert "<li>Built streaming chat</li>" in project.content
    assert "&lt;b&gt;tests&lt;/b&gt;" in project.content


def test_import_twice_skips_everything_the_second_time(client, db):
    client.post("/api/resume/import", json=IMPORT)
    response = client.post("/api/resume/import", json=IMPORT)

    assert response.json() == {"skills_added": 0, "skills_skipped": 2, "projects_added": 0, "projects_skipped": 1}
    assert db.query(Skill).count() == 2
    assert db.query(UserSkill).count() == 2
    assert db.query(Project).count() == 1


def test_import_keeps_an_existing_skill_level(client, db, demo_user):
    skill = Skill(name="python")
    db.add(skill)
    db.commit()
    db.add(UserSkill(user_id=demo_user.id, skill_id=skill.id, proficiency="expert", status="acquired"))
    db.commit()

    client.post("/api/resume/import", json=IMPORT)

    assert db.query(UserSkill).filter_by(skill_id=skill.id).one().proficiency == "expert"


def test_import_links_a_catalog_skill_the_user_has_no_level_for(client, db):
    db.add(Skill(name="React"))
    db.commit()

    response = client.post("/api/resume/import", json=IMPORT)

    assert response.json()["skills_skipped"] == 1
    assert db.query(UserSkill).count() == 2


def test_import_ignores_duplicates_in_the_request(client, db):
    body = {"skills": [{"name": "SQL"}, {"name": "sql"}], "projects": [{"name": "A"}, {"name": "a"}]}

    response = client.post("/api/resume/import", json=body)

    assert response.json() == {"skills_added": 1, "skills_skipped": 0, "projects_added": 1, "projects_skipped": 1}


def test_import_nothing_is_fine(client):
    response = client.post("/api/resume/import", json={})
    assert response.json() == {"skills_added": 0, "skills_skipped": 0, "projects_added": 0, "projects_skipped": 0}


@pytest.mark.parametrize(
    "body",
    [
        {"skills": [{"name": ""}]},
        {"skills": [{"name": "Python", "proficiency": "guru"}]},
        {"skills": [{"name": "x" * 101}]},
        {"projects": [{"name": "  "}]},
    ],
)
def test_import_invalid_items_return_422(client, body):
    assert client.post("/api/resume/import", json=body).status_code == 422
