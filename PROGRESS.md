# Mentora AI: Progress So Far

A record of what has been built, in the order it was done.
For setup and run instructions, see [README.md](README.md).

**Last updated:** 2026-10-19

---

## Summary

| Area | Status |
|---|---|
| AI chat API (normal + streaming) | ✅ Done |
| MCP server at `/mcp` | ✅ Done |
| Database (PostgreSQL, 10 tables, 3 Alembic migrations) | ✅ Done |
| CRUD APIs for all 6 resources | ✅ Done |
| Single demo user (no authentication) | ✅ Done |
| Backend tests (pytest) | ✅ Done (218 tests passing) |
| Frontend setup (React + Vite + Bootstrap) | ✅ Done |
| Frontend pages: Skills, Goals, Career, Projects | ✅ Done |
| AI Mentor chat page (streaming) | ✅ Done |
| Real LLM (Google Gemini) | ✅ Done |
| Mentor uses the user's skills, goals, projects | ✅ Done |
| Conversation history + ChatGPT-style chat list | ✅ Done |
| Dark theme + animated, interactive Mentor UI | ✅ Done |
| Dashboard (stats, goal progress, AI daily tip) | ✅ Done |
| Goals/Career cards, rich project write-ups, chat file uploads | ✅ Done |
| Gemini retries, edit messages, rename chats | ✅ Done |
| Import skills and projects from a resume | ✅ Done |
| Greets the user by name (Keerthi) | ✅ Done |
| Chats, theme and daily tip saved in the database (no localStorage) | ✅ Done |
| Skill levels on the Skills page | ✅ Done |
| Page assistant (floating bot that edits Skills / Goals / Career / Projects) | ✅ Done |
| Authentication (email + password, sign up, per-user data) | ✅ Done |

---

## 1. AI chat and MCP server

**Already in place at the start**

- `POST /api/ai/chat`: returns the mentor's reply as JSON.
- `POST /api/ai/chat/stream`: streams the reply with Server-Sent Events
  (`data: {"token": "..."}` ... `data: [DONE]`).
- Mentor logic in `backend/app/ai/` (`agent.py`, `prompts.py`, `llm_client.py`, `schemas.py`).
- MCP Streamable HTTP server mounted at `/mcp` with two tools, `ask_mentor` and `ping`
  (`mcp<2` is pinned because mcp 2.x renamed `FastMCP`).

> At first the AI was a **mock** that repeated your message. It now calls Gemini
> (see section 9).

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

## 9. Gemini integration

- `backend/app/ai/llm_client.py`: the mock was replaced with Gemini calls through the official
  Google Gen AI SDK (`google-genai>=2,<3`). `generate_response()` for `/api/ai/chat`,
  `stream_response()` for `/api/ai/chat/stream` (real token streaming).
- Settings in `config.py`: `GEMINI_API_KEY` (a `SecretStr`, so it never shows in logs),
  `GEMINI_MODEL` (default `gemini-3.5-flash`), `GEMINI_TIMEOUT_SECONDS` (default 60).
  `backend/.env.example` documents them.
- Failures raise `LLMError` with a user-safe message: `/api/ai/chat` returns `503` (not
  configured / key rejected / model not found / Gemini down), `429` (rate limit) or `504`
  (timeout); the stream sends a `data: {"error": ...}` event with no `[DONE]`. No fake replies.
- If the browser disconnects, the Gemini stream is closed too.
- The frontend and SSE format are unchanged. The MCP `ask_mentor` tool now uses Gemini as well.
- Tests: Gemini is faked (`fake_gemini` fixture); an autouse guard in `conftest.py` fails any
  test that would create a real client.

**Verified:** 68 passed. Live server checked without a key (clean `503` / error event) and against
the real Gemini API with a deliberately invalid key (clean "rejected the API key" error; key not
in the logs). A successful real reply has **not** been checked yet, since no real key was set.

---

## 10. Cleanup and uv

- Removed generated caches, the empty `frontend/public/` and Alembic's placeholder README.
- The backend now uses **uv**: `backend/pyproject.toml` (dependencies, a `dev` group with pytest,
  and the pytest settings) and `backend/uv.lock` replace `requirements.txt` and `pytest.ini`.
- `backend/main.py` starts the server: `uv run main.py` (port 8002, auto-reload on `app/` changes).
- `config.py` finds `backend/.env` by absolute path, so the starting folder doesn't matter.

**Verified:** `uv run pytest`: 68 passed. `uv run main.py` served the root, `/api/skills`, both AI
endpoints (real Gemini replies) and reloaded after a file change.

---

## 11. Personal mentor (user profile in the prompt)

- `backend/app/ai/context.py`: `build_user_profile(db, user_id)` reads the user's skills (catalog
  + skill levels), learning goals with their latest progress, career goals and projects through the
  existing repositories, and formats them as text (max 20 per list, descriptions cut at 300 chars).
- `backend/app/ai/prompts.py`: `build_system_prompt(profile)` adds the profile inside
  `<user_profile>` with instructions to personalise answers and not ask for listed information.
- Both chat endpoints and the MCP `ask_mentor` tool load the profile of the current (demo) user.
  If the database fails, the mentor answers without the profile instead of erroring.
- The profile is background knowledge: greetings get a short "what's on your mind?" reply, and
  skills/goals come up only when the question needs them (e.g. "what should I learn next?").

**Verified:** 73 passed (profile contents, latest progress only, other users' data excluded, empty
profile, database failure, long text shortened). Live with Gemini: asked "What skills do I have?",
it named the saved skills (python, LLM MCp) and suggested adding goals.

---

## 12. Conversation history and chat list

- `ChatRequest` gained `history`: earlier `{role: "user" | "assistant", content}` messages, oldest
  first (max 200 items, 20,000 chars each). `message` and the response/SSE formats are unchanged.
- `app/ai/agent.py`: `recent_history()` keeps the newest `CHAT_HISTORY_LIMIT` messages (default 20,
  `0` = none) and drops a leading reply so history starts with a question.
- `app/ai/llm_client.py`: sends history as Gemini `user` / `model` turns; back-to-back messages from
  the same side (e.g. after a failed reply) are joined into one turn.
- Frontend: `MentorChat.jsx` has a ChatGPT-style sidebar (+ New chat, chats grouped by date, delete
  with confirmation; a slide-in panel on phones). `services/chatStorage.js` saves chats in
  localStorage (max 50). Only real messages are sent as history; failed empty replies are skipped.
- No new database table: chats live in the browser for now.

**Verified:** 84 passed (history order, limit, limit 0, joined turns, invalid history → 422). Live:
Gemini answered a follow-up from history. Browser (Playwright, Chrome): 17 checks passed (follow-up
answered "Teal." from the earlier message, new chat, switching, reload keeps chats, delete, phone
panel, no horizontal scroll).

---

## 13. Dark theme and interactive Mentor UI

- Dark by default for every page (Bootstrap `data-bs-theme`), set in `index.html` before the page
  draws; a sun/moon toggle in the navbar switches to light and is remembered (localStorage).
- New packages: `bootstrap-icons`, `react-markdown` + `remark-gfm` (replies render as Markdown;
  raw HTML is ignored). The Mentor page is lazy-loaded, so other pages don't download them.
- `components/BotAvatar.jsx`: SVG robot that blinks, floats, has a glowing antenna and twinkling
  sparkles, and jitters with darting eyes while a reply is being written.
- Mentor page split into `components/mentor/` (`MentorHome`, `ChatSidebar`, `ChatMessage`).
  It opens on a landing screen (rotating tagline, Start a new chat, Continue last chat, 4
  suggestion cards); typing dots, streaming cursor, message slide-in, copy button, auto-growing
  input. All animations are off when the OS asks for reduced motion.
- Frosted navbar with icons; gradient Add/Save buttons on the CRUD pages.

**Verified:** build OK. Browser (Playwright, Chrome): 20 checks passed (landing first, New chat opens
the chat, suggestion card sends its prompt, bot jitters while thinking, Markdown rendered with no raw
`**`, copy button, theme toggle remembered, no horizontal scroll on a 390px phone); screenshots
reviewed in dark, light, desktop and phone.

---

## 14. Dashboard

- `GET /api/dashboard` (`routers/dashboard.py` → `services/dashboard_service.py` →
  `repositories/dashboard_repository.py`): counts per page (skills, learning/career goals with
  active counts, projects with in-progress count) and up to 20 learning goals with their latest
  progress (completed = 100%, abandoned hidden), active first, nearest target date first.
- `GET /api/ai/tip`: one short personal tip from Gemini based on the profile (same errors as chat).
- `pages/Dashboard.jsx`: greeting with the bot, 4 clickable stat cards with count-up numbers,
  animated gradient progress bars with "in N days" / overdue hints, and a tip card. The tip is
  cached in the browser for the day (1 Gemini call per day); **New tip** asks for another.

**Verified:** 90 passed (counts, other users excluded, latest progress, ordering, tip + errors).
Live: real tip mentioned the user's Python + MCP skills. Browser: stat counts, empty state, tip
cached (1 request per day, StrictMode double request fixed), bars at the right width, links, phone
layout, light theme.

---

## 15. Goals, Career, Projects redesign and file uploads

**Database** (migration `a0783d0b3de9`, additive): new `uploads` table (random 32-hex id, owner,
original name, type, size); `projects.content` (write-up HTML); `career_goals.required_skills`.

**Uploads** (`/api/uploads`, `services/upload_service.py`): files saved to `UPLOAD_DIR`
(`backend/uploads`, git-ignored), max `MAX_UPLOAD_MB` (20). The type comes from the file's first
bytes, not its name: PNG, JPEG, WebP, GIF, PDF, or UTF-8 text/code by extension. SVG, Office files,
video etc. are rejected. Text is always served as `text/plain` + `nosniff`, so uploaded HTML can't run.
Users only see their own files.

**Chat attachments**: up to 5 files per message (`attachments` ids on the message and on history
items; a message may be files only). `app/ai/attachments.py` loads them newest first within an 18 MB
inline budget; images/PDFs go to Gemini as bytes, text files as text; files left out or deleted are
replaced by a note. Frontend `Composer.jsx`: paperclip, drag & drop over the chat, paste, upload
progress, remove; messages show image thumbnails and file chips.

**Goals**: cards with a progress ring; "Update progress" dialog (slider, +/- steps, note, history,
"mark completed" at 100%, confetti). The API now returns `progress_percent` / `last_progress_at`
(completed = 100%).

**Career**: only role, needed skills and notes. Cards show readiness (needed skills you already have
on the Skills page), chips to add/remove needed skills in place (saved instantly), "I have this" adds
a skill to Skills, re-syncs when the tab regains focus, "Ask Mentora for a roadmap" opens the chat with
a prepared question.

**Projects**: cards with the write-up's first image as cover; `/projects/:id` with a TipTap rich editor
(headings, bold/italic/underline/strike, lists, quote, code, links, images by button/paste/drop, undo,
Ctrl+S). Images are stored as `/api/uploads/<id>`. The mentor's profile includes a text preview of the
write-up and each role's needed skills.

**Verified:** 123 backend tests. Live Gemini (before the free quota ran out): read a screenshot and
found a bug in an attached .py file. Browser: 28/28 checks for Goals/Career/Projects, using `[test]`
data that was deleted afterwards, plus chat attachments UI. Found and fixed: toolbar clicks stole the
editor's focus (lost keystrokes and bold).

---

## 16. Reliability and chat editing

- **Gemini retries:** brief 500/502/503/504 errors (e.g. "model overloaded") and dropped connections
  are retried by the SDK, up to 3 attempts (~1 s, ~2 s). 429 is not retried; the message now says
  whether it's the daily free limit or the per-minute one, and when it resets. `GEMINI_MODEL` was set
  to `gemini-3.5-flash-lite` in `backend/.env` after the free daily limit (20/day per model) ran out.
- **Edit a sent message:** "Edit" under your message; the replies after it are replaced and the
  mentor answers the edited text (history = only the messages before it). Marked "(edited)".
- **Rename a chat:** pencil next to each chat in the sidebar (or double-click the name).
- **Phone menu:** the hamburger menu is React-controlled and closes on link tap, outside tap,
  Escape and page change. Bigger navbar logo.

**Verified:** 130 backend tests (3 run the real SDK against a fake server: 503 → retry → OK, gives up
after 3, 429 not retried). Browser: 14/14 edit + rename checks, 11/11 phone menu checks.

---

## 17. Import skills and projects from a resume

Two steps, so nothing is saved without the user seeing it:

- **`POST /api/resume/parse`** `{upload_id}`: Gemini reads the uploaded resume (PDF, PNG/JPEG/WebP,
  or text; GIF → 400) in JSON mode (`llm_client.generate_json`, schema in `app/ai/resume.py`). The
  answer is tidied (trimmed, de-duplicated ignoring case, clipped to column sizes, unknown levels →
  intermediate). Each skill/project says `already_saved` (skill in the catalog / project with that name).
- **`POST /api/resume/import`** `{skills, projects}`: missing skills are added to the catalog and
  linked in `user_skills` with the resume's level and status `acquired` (an existing level is kept);
  projects are created as `completed`, technologies comma-joined, and the resume's bullet points
  (HTML-escaped) become the write-up. Duplicates are skipped, so importing twice is safe.
- **Frontend:** "Import from resume" on the Skills and Projects pages (`ResumeImportModal.jsx`):
  drop/choose a file → "Reading your resume..." → toggle skill chips and project cards (new ones
  pre-selected) → Import → summary. The uploaded file is deleted once it has been read.

**Verified:** 151 backend tests (21 new in `test_resume.py`, Gemini faked). Live Gemini on a sample
PDF: 6 skills with sensible levels ("5 years" → advanced, "basic" → beginner), 2 projects, the job
itself not listed as a project, ~2 s.

---

## 18. Greeting the user by name

- **`GET /api/me`** returns the current user; **`PATCH /api/me`** `{full_name}` renames them
  (`routers/me.py`). The dev user is now named "Keerthi".
- **Frontend:** `hooks/useMe.js` (one shared request; the placeholder "Demo User" is never shown).
  Dashboard: "Good morning, Keerthi! 👋" with a pencil to change the name. Mentor home: "Hi Keerthi,
  I'm Mentora".
- **Mentor:** the prompt tells Gemini to call the user by first name when greeting, not in every message.

**Verified:** 157 backend tests (6 new in `test_me.py`). Live: "hi" → "Hi Keerthi! It's great to hear from you…".

---

## 19. Everything saved in the database (no localStorage)

**Database** (migration `909b0d3d06d8`, additive): `conversations` (id made by the browser, title,
created/updated time) and `chat_messages` (position, role, content, attachments as JSON, error /
stopped / edited); `users.theme`, `users.daily_tip`, `users.daily_tip_date`.

- **Chats:** `/api/conversations`: list (newest first, no messages), get one, `PUT` (create or replace
  the whole chat), `PATCH` (rename), `DELETE`. Other users' chats → 404. Replies still stream from
  `/api/ai/chat/stream`; the chat page saves the conversation when the reply is done, loads a chat's
  messages when it is opened, and shows a warning if a save fails (and retries with the next change).
- **Theme:** `PATCH /api/me {theme}`; applied when the user loads (the `index.html` pre-paint script is gone,
  so light mode shows dark for a moment on reload).
- **Daily tip:** `GET /api/ai/tip` returns today's saved tip; `?refresh=true` ("New tip") asks for a new one.
- **One-time move:** chats and theme an older version left in the browser were copied into the
  database once and deleted from localStorage; that code was removed afterwards.

**Verified:** backend tests; live: the open browser moved 3 chats (original dates kept) and the light
theme into the database; save/load/delete of a test chat; tip saved for the day.

---

## 20. Skill levels on the Skills page

- The Skills table now has **Your level** (beginner → expert) and **Status** (want to learn, learning,
  acquired) dropdowns per skill, saved right away through `/api/user-skills`. "Set level..." removes
  the level; status is disabled until a level is set.
- The add/edit form also sets the level and status. Filter pills: All, Want to learn, Learning,
  Acquired, Not set.
- `components/CrudPage.jsx` was removed: the Skills page was its only user and now has its own table.

**Verified:** Playwright, 15/15 checks (add with level, change level and status in place, filters,
remove level, edit, delete, no console errors) using a `[test]` skill that was deleted afterwards.

---

## 21. Page assistant (floating bot that changes page data)

- **Backend:** `POST /api/ai/assistant` `{page, message, history}`. `app/ai/assistant.py` gives Gemini
  the tools for that page only (Skills: `set_skill`, `rename_skill`, `clear_skill_level`,
  `delete_skill`; Goals: `add_goal`, `update_goal`, `log_progress`, `delete_goal`; Career and Projects:
  add / update / delete) plus the page's current items. `llm_client.generate_with_tools` runs the loop
  (max 6 rounds), sending Gemini's turn back unchanged so its thought signatures are kept.
- Tools use the normal services and schemas: bad values, unknown names/ids, other users' data and
  duplicates come back to Gemini as `{"error": ...}`, and nothing half-done is saved. Deletes only
  after the user confirms. If Gemini fails after a change, the reply still lists what was done.
- **Frontend:** `components/PageAssistant.jsx`, a bot button (bottom right) on the 4 pages that opens a
  small chat with example requests; the changes are listed with ✓ and the page reloads its data.
  The little chat isn't saved (fresh on each visit).

**Verified:** 15 new tests (fake Gemini scripting tool calls). Live with Gemini: add → change level →
asks to confirm → delete. Playwright 9/9: bot on all 4 pages, a change shows in the table without a
reload, fits a phone screen, no console errors (test data deleted).

---

## 22. Smaller text on the Mentor page

- Messages, chat list and message box: 16px → **15px** (`.chat-page` in `index.css`); chat title
  20px → 16px; the landing heading, subtitle and buttons use normal sizes instead of display / large.

**Verified:** sizes measured in the browser (Playwright); screenshots of the landing and an open chat.

---

## 23. Health check and startup report

- **Full check (2026-10-19):** backend, database on the latest migration, all list endpoints 200,
  MCP `tools/list` (ask_mentor, ping), `ping`, `ask_mentor` with real Gemini, frontend: all working.
- **Startup report** (`app/startup_report.py`): when the backend starts it prints one ✓ / ✗ line for
  the database, migrations (current vs. latest), user, data counts, Gemini key and model (not called,
  to save quota), uploads folder (writable) and MCP tools. A ✗ says how to fix it; if the database is
  down the checks that need it are skipped. The demo-user seed error is now one line, not a traceback.
- **MCP tool lines:** each call prints `MCP ▶ <tool> called` and `MCP ✓ <tool> done in 1.2s` (or ✗ failed).
- FastMCP turned on INFO logging for every library (alembic plugins, raw Gemini HTTP lines);
  `log_level="WARNING"` hides that noise so the report stands out.

**Verified:** 4 new tests; a second copy on port 8099 showed the report and MCP lines, and with the
database down and no Gemini key it showed the ✗ lines with hints (copies stopped afterwards).

---

## 24. Private settings only in `.env`

- Removed from the code: the database URL with its password (`config.py` default), the CORS origins
  (`main.py`), the backend host/port (`backend/main.py`) and the frontend's fallback backend URL
  (`api.js`). They are now required settings: `DATABASE_URL`, `API_HOST`, `API_PORT`, `CORS_ORIGINS`
  in `backend/.env`, and `VITE_API_BASE_URL` in `frontend/.env`.
- `backend/.env.example` and the new `frontend/.env.example` use a placeholder `YOUR_DB_PASSWORD`; the
  README no longer shows the real database password.
- Checked: both `.env` files are git-ignored and were never committed; no Gemini key in the git history.

**Verified:** 197 tests; the live backend reloaded with the new settings; CORS allows
`http://localhost:5173` and rejects other sites; the frontend loads data with no console errors.

---

## 25. Authentication

**Database** (migration `d8d0a4fedbd1`): `users.password_hash`; new `sessions` table (SHA-256 of the
login token, user, expiry); **skills now belong to a user** (`skills.user_id`, names unique per user).
Before, the skills list was shared by everyone. The migration gave the existing 34 skills to their
owner (Keerthi). Tested on a copy of the database first (up, down, up); a backup was taken.

- **Backend:** `POST /api/auth/register|login|logout`. Passwords hashed with scrypt (stdlib,
  `app/security.py`); a wrong email and a wrong password give the same 401 and take the same time.
  The login is a random token in an httpOnly, SameSite=Lax cookie (`SESSION_DAYS`, default 30);
  only its hash is stored, and log out deletes the session. `get_current_user_id()` now reads the
  cookie (401 if missing/expired/forged). The demo-user seed and `DEMO_USER_ID` were removed.
- **MCP:** `/mcp` needs `Authorization: Bearer <MCP_TOKEN>` (random token added to `backend/.env`);
  tools act as `MCP_USER_ID`. Without a token configured, `/mcp` refuses everything.
- **Account command:** `uv run python -m app.manage list-users` / `set-login --user-id 1 --email ...`
  (password typed in, twice), to give the existing account a login.
- **Frontend:** Log in and Sign up pages (shown at any address while logged out; after logging in,
  that page opens), Log out button in the navbar, back to the login page on any 401. Vite now
  proxies `/api` to the backend (`BACKEND_URL` in `frontend/.env`, not sent to the browser), so the
  cookie works across the two ports; no token is ever handled in JavaScript.
- **Startup report:** "Users: N accounts, M can log in" and MCP "acts as <name>".

**Verified:** 21 new tests (sign up, log in/out, same 401 for wrong email/password, expired and forged
cookies, every page needs a login, each account sees only its own data, other users' skills → 404,
set-login, MCP token). Live: `/mcp` 401 without/with a wrong token, works with the right one.
Playwright 13/13 with a `[test]` account (deleted afterwards): sign up, own empty data, add a skill,
still logged in after refresh, log out, wrong password, log in back to the same page, cookie is
httpOnly and invisible to JavaScript.

## 26. One .env file

`frontend/.env` and `frontend/.env.example` are gone; `backend/.env` is the project's only `.env`.
The Vite dev server reads `API_HOST` and `API_PORT` from it for the `/api` proxy (in the config
only, never sent to the browser). The stale `DEMO_USER_ID` was removed from `backend/.env.example`.
`API_HOST`, `API_PORT` (default 127.0.0.1:8002) and `CORS_ORIGINS` (default none) are now
optional, so the backend starts on Render, which runs uvicorn with its own `--host`/`--port`.

---

## Next steps (not started)

1. pytest tests for career goals and projects CRUD; automated frontend tests.
2. Password reset by email and email verification.
