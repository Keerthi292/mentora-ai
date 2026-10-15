# Mentora AI: Progress So Far

A record of what has been built, in the order it was done.
For setup and run instructions, see [README.md](README.md).

**Last updated:** 2026-10-15

---

## Summary

| Area | Status |
|---|---|
| AI chat API (mock LLM, normal + streaming) | ✅ Done |
| MCP server at `/mcp` | ✅ Done |
| Database (PostgreSQL, 7 tables, Alembic migration) | ✅ Done |
| CRUD APIs for all 6 resources | ✅ Done |
| Single demo user (no authentication) | ✅ Done |
| Backend tests (pytest) | ✅ Done (50 tests passing) |
| Frontend setup (React + Vite + Bootstrap) | ✅ Done |
| Frontend pages: Skills, Goals, Career, Projects | ✅ Done |
| AI Mentor chat page (streaming) | ✅ Done |
| Real LLM | ⏳ Not started (mock only) |
| Authentication | ⏳ Not started (on purpose) |

---

## 1. AI chat and MCP server

**Already in place at the start**

- `POST /api/ai/chat`: returns the mentor's reply as JSON.
- `POST /api/ai/chat/stream`: streams the reply with Server-Sent Events
  (`data: {"token": "..."}` ... `data: [DONE]`).
- Mentor logic in `backend/app/ai/` (`agent.py`, `prompts.py`, `llm_client.py`, `schemas.py`).
- MCP Streamable HTTP server mounted at `/mcp` with two tools, `ask_mentor` and `ping`
  (`mcp<2` is pinned because mcp 2.x renamed `FastMCP`).

> The AI is a **mock**: `llm_client.py` returns a fixed sentence that repeats your
> message. No LLM (OpenAI, Claude, Gemini, ...) is connected.

---

## 2. Database foundation

`config.py`, `database.py` and `models.py` were empty, so the foundation was built from scratch.

- **PostgreSQL 16 in Docker:** container `mentora-postgres`, volume `mentora_pgdata`, port 5432.
- **`config.py`:** reads `DATABASE_URL` from `backend/.env` (pydantic-settings).
- **`database.py`:** SQLAlchemy engine, session factory, `Base`, and the `get_db()` dependency.
- **`models.py`:** 7 tables using SQLAlchemy 2.x `Mapped` / `mapped_column`:
  - `users`: id, email (unique), full_name, created_at
  - `skills`: id, name (unique), category
  - `learning_goals`: user_id, title, description, status, target_date, created_at
  - `user_skills`: user_id, skill_id, proficiency, status; unique on (user_id, skill_id)
  - `learning_progress`: learning_goal_id, progress_percent (CHECK 0–100), note, created_at
  - `career_goals`: user_id, target_role, description, status, target_date
  - `projects`: user_id, name, description, technologies, status
  - Every foreign key has an index and `ON DELETE CASCADE`; relationships go both ways.
- **Alembic:** set up, reads the URL from the app settings; migration
  `e770cc3cb917_create_initial_tables.py`.

**Verified:** upgrade, downgrade and re-upgrade all work; `alembic check` shows no
differences; the unique, check and cascade rules were tested with real rows.

---

## 3. CRUD APIs (router → service → repository)

**Skills and learning goals**

- Files: `repositories/skill_repository.py`, `repositories/learning_goal_repository.py`,
  `services/skill_service.py`, `services/learning_goal_service.py`,
  `routers/skills.py`, `routers/learning_goals.py`.
- Pydantic Create / Update / Response schemas in `schemas.py`; statuses use `Literal` types.
- Status codes: 201 on create, 204 on delete, 404 when not found, 409 for a duplicate skill
  name (ignores case and spaces), 422 for invalid input.
- PATCH only changes the fields that are sent; `null` in a required field is rejected.

**User skills, learning progress, career goals, projects**

- Same pattern and structure.
- User skills: 404 for an unknown skill, 409 if the user already has the skill; the response
  includes the skill's details.
- Learning progress lives under its goal: `/api/learning-goals/{goal_id}/progress`.
- Shared helpers: `repositories/user_repository.py`, `services/user_service.py`.

**Verified:** live requests against every endpoint; 75 checks passed on the first run of
the four new resources.

---

## 4. Backend tests (pytest)

- Added `pytest` and `httpx` to `requirements.txt`, and fixed a broken line
  (`python-dotenvmcp[cli]` → `python-dotenv` + `mcp[cli]<2`).
- `backend/pytest.ini`, `backend/tests/conftest.py`:
  - Separate PostgreSQL test database `mentora_test`, created automatically.
  - Each test runs in a transaction that is rolled back, so tests don't affect each other.
  - `get_db` is overridden; a `demo_user` fixture creates the demo user.
- Test files:
  - `test_ai_chat.py` (4): valid message; empty, spaces-only or missing message → 422
  - `test_skills.py` (20): full CRUD, 409 duplicates, 404s, 422s, sorting and paging
  - `test_learning_goals.py` (21): full CRUD as the demo user, other users' goals → 404
  - `test_demo_user.py` (5): seed creates the user, is safe to run twice, keeps ids in sync

**Verified:** 50 passed. Deliberately breaking the duplicate check or the ownership filter
made the right tests fail.

---

## 5. Single demo user (no authentication)

- `config.py`: `DEMO_USER_ID = 1` (can be overridden in `.env`).
- `app/seed.py`: creates `Demo User` / `demo@mentora.local` only if it doesn't exist; safe
  to run any number of times; keeps the id counter in sync. Run it manually with
  `python -m app.seed`.
- `app/dependencies.py`: `get_current_user_id()` returns the demo user's id
  ("Replace this with real authentication later.").
- `main.py`: seeds the demo user on startup, before the MCP session manager starts. If the
  database is down, it logs an error and the app still starts.
- All user-scoped routers use `get_current_user_id`; the old `?user_id=` parameter was
  removed.
- `password_hash` was **not** added (no auth for now).

**Verified:** the demo user exists in the database; uvicorn starts on a fresh database, on
restart, and with PostgreSQL stopped.

---

## 6. Frontend setup

- Created `package.json`, `vite.config.js` (port 5173, fixed) and `index.html` in `frontend/`.
- Installed React, React Router, Bootstrap and Vite.
- `frontend/.env`: `VITE_API_BASE_URL=http://127.0.0.1:8002`.
- `src/services/api.js`: small `fetch` wrapper (`api.get/post/patch/delete`), no auth
  headers, readable error messages.
- `src/layouts/MainLayout.jsx`: Bootstrap navbar (Dashboard, Skills, Goals, Career,
  Projects, Mentor), collapses on phones.
- `src/pages/Dashboard.jsx`: placeholder with a backend online/offline indicator.

**Verified:** `npm run dev` and `npm run build` work; the page called the backend in a real
browser (CORS OK).

---

## 7. Frontend CRUD pages

- Pages: `Skills.jsx` (`/skills`), `LearningGoals.jsx` (`/goals`), `CareerGoals.jsx`
  (`/career`), `Projects.jsx` (`/projects`).
- Each page lists items in a table and uses Bootstrap modals to add, edit and delete
  (with a confirmation).
- Shared code: `components/CrudPage.jsx`, `FormModal.jsx`, `Modal.jsx`,
  `ConfirmDeleteModal.jsx`, `StatusBadge.jsx`, `hooks/useResource.js`, `utils/format.js`.
- Backend errors (e.g. "A skill named 'python' already exists") show inside the modal.

**Verified in Chrome:** add, edit and delete on all four pages, error messages, navbar
links, and the phone layout.

---

## 8. AI Mentor chat page

- `src/pages/MentorChat.jsx` (`/mentor`): Bootstrap chat layout with a message list and an
  input box.
- `src/services/mentorChat.js`: calls `POST /api/ai/chat/stream` with `fetch` and
  `response.body.getReader()`.
- `src/services/sse.js`: parses the `data:` lines, buffering until each event is complete.
- Shows each word as it arrives and stops on `[DONE]`.
- "Thinking..." while waiting; input disabled and a **Stop** button while the reply streams.
- Enter sends, Shift+Enter adds a new line.
- Errors (backend down, 422, error event, stream cut off) show in the reply bubble.

**Verified:** 10 parser unit tests and 23 browser checks passed. One bug was found and fixed:
the input box now gets focus back after a reply.

---

## Next steps (not started)

1. Connect a real LLM (e.g. Claude) in `backend/app/ai/llm_client.py`.
2. Send the conversation history so the mentor remembers earlier messages.
3. Give the mentor the user's skills, goals and projects for personalized advice.
4. Dashboard content (summary of goals, progress, skills).
5. UI for user skills and learning progress (the backend APIs already exist).
6. pytest tests for user skills, learning progress, career goals and projects.
7. Authentication (later, by replacing `get_current_user_id()`).
