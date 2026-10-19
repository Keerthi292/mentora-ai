"""Tests for POST /api/ai/assistant (the page assistant that changes page data).

Gemini is replaced by a fake that answers with scripted tool calls, then text.
"""

import pytest
from google.genai import errors, types

from app.ai import llm_client
from app.models import CareerGoal, LearningGoal, LearningProgress, Project, Skill, UserSkill

URL = "/api/ai/assistant"

pytestmark = pytest.mark.usefixtures("demo_user")


def _call(tool: str, /, **args) -> types.GenerateContentResponse:
    part = types.Part(function_call=types.FunctionCall(name=tool, args=args))
    return types.GenerateContentResponse(candidates=[types.Candidate(content=types.Content(role="model", parts=[part]))])


def _text(text: str) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part(text=text)]))]
    )


class FakeGemini:
    """Answers with `self.script` in order: tool calls, text, or an exception."""

    def __init__(self):
        self.script = []
        self.calls = []
        self.models = self

    def generate_content(self, **kwargs):
        # Copy: the client keeps appending to the same list
        self.calls.append({**kwargs, "contents": list(kwargs["contents"])})
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


@pytest.fixture
def gemini(monkeypatch):
    fake = FakeGemini()
    monkeypatch.setattr(llm_client, "_create_client", lambda *args, **kwargs: fake)
    return fake


def _tool_names(call) -> list[str]:
    return [d.name for d in call["config"].tools[0].function_declarations]


def _tool_results(call) -> list[dict]:
    """The function results sent back to Gemini in this request."""
    return [p.function_response.response for p in call["contents"][-1].parts]


# --- Skills ------------------------------------------------------------------------


def test_sets_the_level_of_an_existing_skill(client, gemini, db, demo_user):
    skill = Skill(user_id=1, name="Docker", category="DevOps")
    db.add(skill)
    db.commit()
    gemini.script = [_call("set_skill", name="docker", proficiency="advanced", status="learning"), _text("Done!")]

    response = client.post(URL, json={"page": "skills", "message": "set docker to advanced"})

    assert response.status_code == 200
    assert response.json() == {
        "reply": "Done!",
        "actions": ["Updated Docker (DevOps, advanced, learning)"],
        "changed": True,
    }
    level = db.query(UserSkill).one()
    assert (level.skill_id, level.proficiency, level.status) == (skill.id, "advanced", "learning")
    # Gemini saw this page's data and only this page's tools
    first = gemini.calls[0]
    assert "- Docker: DevOps; level not set" in first["config"].system_instruction
    assert _tool_names(first) == ["set_skill", "rename_skill", "clear_skill_level", "delete_skill"]
    assert _tool_results(gemini.calls[1]) == [
        {"ok": True, "name": "Docker", "category": "DevOps", "proficiency": "advanced", "status": "learning"}
    ]


def test_adds_a_new_skill(client, gemini, db):
    gemini.script = [_call("set_skill", name="Kubernetes", category="DevOps", proficiency="beginner"), _text("Added.")]

    body = client.post(URL, json={"page": "skills", "message": "add kubernetes"}).json()

    assert body["actions"] == ["Added Kubernetes (DevOps, beginner, learning)"]
    assert db.query(Skill).one().name == "Kubernetes"


def test_tool_errors_go_back_to_gemini_and_change_nothing(client, gemini, db):
    gemini.script = [_call("rename_skill", name="Rust", new_name="Rust lang"), _text("There's no Rust skill.")]

    body = client.post(URL, json={"page": "skills", "message": "rename rust"}).json()

    assert body == {"reply": "There's no Rust skill.", "actions": [], "changed": False}
    assert _tool_results(gemini.calls[1]) == [{"error": "No skill named 'Rust' on the Skills page"}]


def test_invalid_values_from_gemini_are_rejected(client, gemini, db):
    gemini.script = [_call("set_skill", name="Go", proficiency="guru"), _text("Sorry.")]

    body = client.post(URL, json={"page": "skills", "message": "go guru"}).json()

    assert body["changed"] is False
    assert "proficiency" in _tool_results(gemini.calls[1])[0]["error"]
    # Checked before anything is saved: no half-made skill
    assert db.query(Skill).count() == 0
    assert db.query(UserSkill).count() == 0


def test_tools_of_another_page_are_refused(client, gemini, db):
    gemini.script = [_call("add_project", name="Sneaky"), _text("Can't do that here.")]

    body = client.post(URL, json={"page": "skills", "message": "add a project"}).json()

    assert body["changed"] is False
    assert _tool_results(gemini.calls[1]) == [{"error": "Unknown tool add_project"}]
    assert db.query(Project).count() == 0


# --- Goals, career, projects -------------------------------------------------------


def test_logs_progress_on_a_goal(client, gemini, db, demo_user):
    goal = LearningGoal(user_id=demo_user.id, title="Learn RAG")
    db.add(goal)
    db.commit()
    gemini.script = [_call("log_progress", goal_id=goal.id, progress_percent=60, note="Built a demo"), _text("Nice!")]

    body = client.post(URL, json={"page": "goals", "message": "rag is 60% done"}).json()

    assert body["actions"] == ['"Learn RAG" is now at 60%']
    entry = db.query(LearningProgress).one()
    assert (entry.progress_percent, entry.note) == (60, "Built a demo")
    assert f"- id {goal.id}: Learn RAG [active, 0%]" in gemini.calls[0]["config"].system_instruction


def test_cannot_change_another_users_goal(client, gemini, db, make_user):
    goal = LearningGoal(user_id=make_user().id, title="Theirs")
    db.add(goal)
    db.commit()
    gemini.script = [_call("delete_goal", goal_id=goal.id), _text("Not found.")]

    body = client.post(URL, json={"page": "goals", "message": "delete it"}).json()

    assert body["changed"] is False
    assert db.get(LearningGoal, goal.id) is not None


def test_updates_a_career_goal(client, gemini, db, demo_user):
    career = CareerGoal(user_id=demo_user.id, target_role="AI Engineer", required_skills="Python")
    db.add(career)
    db.commit()
    gemini.script = [_call("update_career_goal", career_goal_id=career.id, required_skills="Python, Docker"), _text("Ok")]

    body = client.post(URL, json={"page": "career", "message": "add docker"}).json()

    assert body["actions"] == ['Updated "AI Engineer": required skills Python, Docker']
    assert career.required_skills == "Python, Docker"


def test_adds_then_deletes_projects_in_one_message(client, gemini, db, demo_user):
    old = Project(user_id=demo_user.id, name="Old app")
    db.add(old)
    db.commit()
    gemini.script = [
        _call("add_project", name="New app", technologies="React", status="in_progress"),
        _call("delete_project", project_id=old.id),
        _text("Added New app and deleted Old app."),
    ]

    body = client.post(
        URL,
        json={
            "page": "projects",
            "message": "yes, delete it",
            "history": [
                {"role": "user", "content": "add New app and delete Old app"},
                {"role": "assistant", "content": "Delete Old app? Please confirm."},
            ],
        },
    ).json()

    assert body["actions"] == ['Added project "New app"', 'Deleted project "Old app"']
    assert [p.name for p in db.query(Project).all()] == ["New app"]
    # The earlier conversation was sent too
    assert [c.role for c in gemini.calls[0]["contents"]] == ["user", "model", "user"]


# --- Failures ------------------------------------------------------------------------


def test_gemini_error_before_any_change_is_an_http_error(client, gemini):
    gemini.script = [errors.ClientError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "quota"}})]

    response = client.post(URL, json={"page": "skills", "message": "hi"})

    assert response.status_code == 429


def test_gemini_error_after_a_change_still_reports_it(client, gemini, db):
    gemini.script = [
        _call("set_skill", name="SQL"),
        errors.ServerError(503, {"error": {"code": 503, "status": "UNAVAILABLE", "message": "overloaded"}}),
    ]

    response = client.post(URL, json={"page": "skills", "message": "add sql"})

    assert response.status_code == 200
    body = response.json()
    assert body["changed"] is True
    assert "Already done: Added SQL" in body["reply"]


def test_too_many_tool_rounds_stops(client, gemini, db):
    gemini.script = [_call("set_skill", name=f"S{i}") for i in range(llm_client.MAX_TOOL_ROUNDS)]

    body = client.post(URL, json={"page": "skills", "message": "loop"}).json()

    assert "too many steps" in body["reply"]
    assert len(gemini.calls) == llm_client.MAX_TOOL_ROUNDS


@pytest.mark.parametrize(
    "body",
    [
        {"page": "dashboard", "message": "hi"},
        {"page": "skills", "message": "   "},
        {"page": "skills"},
    ],
)
def test_invalid_requests_return_422(client, gemini, body):
    assert client.post(URL, json=body).status_code == 422
