# Mentora AI

AI-powered personal learning and career companion. Track your skills, learning goals,
career goals and projects, and chat with an AI mentor that knows all of them.

## Contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [How it works](#how-it-works)
- [API reference](#api-reference)
- [AI mentor](#ai-mentor)
- [Development](#development)
- [Roadmap](#roadmap)

---

## Features

| Page | URL | What it does |
|---|---|---|
| Dashboard | `/` | Greeting by name, counts per page, learning-goal progress, AI tip of the day |
| Skills | `/skills` | Level and status per skill (edit in place), filters, **Import from resume** |
| Learning Goals | `/goals` | Progress rings; log progress with a slider, note and history |
| Career Goals | `/career` | Target roles with required skills, readiness ring, AI roadmap |
| Projects | `/projects` | Cards with cover images, **Import from resume**, rich-text write-ups at `/projects/:id` |
| AI Mentor | `/mentor` | ChatGPT-style chat: streaming replies, chat history, rename, edit messages, file uploads |

- **Page assistant:** a floating bot on Skills, Goals, Career and Projects changes that page's
  data from plain-language requests ("set Docker to advanced", "I'm 60% done with my RAG goal").
  It asks before deleting anything.
- **Accounts:** email + password sign-up, "forgot password" with a 6-digit code by email; each account sees
  only its own data.
- **Dark theme** by default (light toggle in the navbar), responsive on phones.
- **MCP server** at `/mcp` so external AI clients can ask the mentor (optional).

---

## Tech stack

| Part | Technologies |
|---|---|
| Frontend | React 19, Vite 8, React Router 7, Bootstrap 5 + Bootstrap Icons, react-markdown, TipTap |
| Backend | Python 3.12+, FastAPI, Pydantic, SQLAlchemy 2, Alembic |
| Database | PostgreSQL 16 (Docker locally) |
| AI | Google Gemini (`google-genai`): SSE streaming, file attachments, retries, tool calling; MCP server |
| Tests | pytest + httpx |
| Hosting | Vercel (frontend), Render (backend) |

---

## Getting started

**Prerequisites:** Python 3.12+ with [uv](https://docs.astral.sh/uv/) (or pip), Node.js 20.19+, Docker.

### 1. Database

```bash
# First time
docker run -d --name mentora-postgres \
  -e POSTGRES_USER=mentora -e POSTGRES_PASSWORD=YOUR_DB_PASSWORD -e POSTGRES_DB=mentora \
  -p 5432:5432 -v mentora_pgdata:/var/lib/postgresql/data \
  --restart unless-stopped postgres:16

# Later, if it's stopped
docker start mentora-postgres
```

### 2. Backend

```bash
cd backend
cp .env.example .env            # then set DATABASE_URL and GEMINI_API_KEY (see Configuration)
uv run alembic upgrade head     # create the tables
uv run main.py                  # http://127.0.0.1:8002, reloads when app/ changes
```

`uv run` creates `.venv` and installs from `uv.lock` on first use. To use pip instead:
`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python main.py`.

On startup the backend prints one ✓ / ✗ line per part; a ✗ line explains how to fix it:

```text
INFO:     ── Mentora AI ──────────────────────────────────────────────
INFO:     ✓ Database    connected to mentora on localhost:5432
INFO:     ✓ Migrations  up to date (d8d0a4fedbd1)
INFO:     ✓ Users       1 account, 1 can log in
INFO:     ✓ Data        34 skills, 0 learning goals, 6 projects, 4 chats
INFO:     ✓ Gemini      key set, model gemini-3.5-flash-lite (not called now, to save quota)
INFO:     ✓ Uploads     .../backend/uploads (2 files, max 20 MB each)
INFO:     ✓ MCP         /mcp (Bearer token), acts as "Keerthi", tools: ask_mentor, ping
INFO:     ── All systems ready · API docs at /docs ──────────────────────
```

API docs (Swagger): http://127.0.0.1:8002/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

The frontend has no `.env`. The Vite dev server reads `API_HOST` / `API_PORT` from
`backend/.env` and proxies `/api` to the backend, so the login cookie is same-origin.
Nothing from `backend/.env` reaches the browser.

---

## Configuration

All settings live in `backend/.env` (git-ignored; template in `backend/.env.example`).
Secrets are never in code.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | **required** | `postgresql+psycopg2://mentora:PASSWORD@localhost:5432/mentora` (`postgres://` URLs are converted) |
| `GEMINI_API_KEY` | none | Needed for every AI feature. Get one at [Google AI Studio](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Switch models without code changes |
| `GEMINI_TIMEOUT_SECONDS` | `60` | Give up on a Gemini request after this long |
| `CHAT_HISTORY_LIMIT` | `20` | Earlier messages sent with each new one (`0` = none) |
| `MAX_UPLOAD_MB` | `20` | Max size per uploaded file |
| `UPLOAD_DIR` | `backend/uploads` | Where uploaded files are stored |
| `API_HOST` / `API_PORT` | `127.0.0.1` / `8002` | Where `uv run main.py` listens (the Vite proxy uses them too) |
| `CORS_ORIGINS` | empty | Extra browser origins, comma-separated. Not needed when `/api` is proxied |
| `SESSION_DAYS` | `30` | How long a login lasts |
| `COOKIE_SECURE` | `false` | Set `true` when served over HTTPS |
| `SMTP_HOST` / `SMTP_PORT` | empty / `587` | Mail server for reset emails (Gmail: `smtp.gmail.com` + an [app password](https://myaccount.google.com/apppasswords)). Empty = the code is printed in the backend terminal |
| `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` | empty | Mail login and sender (`SMTP_FROM` defaults to `SMTP_USER`) |
| `RESET_CODE_MINUTES` / `RESET_CODE_ATTEMPTS` | `15` / `5` | How long a reset code works, and how many wrong tries it allows |
| `MCP_TOKEN` | none | Bearer token for `/mcp`. Without it, `/mcp` refuses every request |
| `MCP_USER_ID` | none | The account MCP tools act as |

Generate an MCP token with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

---

## Deployment

- **Frontend:** Vercel, project root `frontend`. `frontend/vercel.json` rewrites `/api/*` to the
  Render backend (so the login cookie stays same-site) and every other path to `index.html`.
  Update the backend URL there if it moves.
- **Backend:** Render, running uvicorn with its own host/port. Set `DATABASE_URL`,
  `GEMINI_API_KEY` and `COOKIE_SECURE=true` in its environment.

---

## How it works

The backend is layered: **router → service → repository → database**. Routers handle HTTP,
services hold the rules (404 / 409 checks, ownership), repositories run the queries.
`get_current_user_id()` reads the login cookie (401 without one) and every query is filtered by
that user, so another user's data always returns 404.

```mermaid
flowchart TB
    user(["You (browser)"])

    subgraph FE["Frontend: React + Vite"]
        direction LR
        pages["Pages<br/>Dashboard, Skills, Goals,<br/>Career, Projects, Mentor"] --> services["services/<br/>api.js, chats.js, sse.js, uploads.js"]
    end

    subgraph BE["Backend: FastAPI"]
        direction LR
        routers["routers/<br/>HTTP endpoints"] --> svc["services/<br/>rules, 404 / 409 checks"] --> repos["repositories/<br/>database queries"]
        routers --> ai["ai/<br/>prompts, profile, Gemini client"]
        mcp["MCP server<br/>/mcp"] --> ai
        ai -- "your profile" --> repos
    end

    subgraph EXT["Storage and services"]
        direction LR
        db[("PostgreSQL<br/>users, skills, goals, projects,<br/>chats, uploads, ...")]
        files[("backend/uploads/<br/>uploaded files")]
        gemini["Google Gemini API"]
    end

    user --> FE
    services -- "JSON over HTTP (chat replies as SSE)" --> routers
    repos --> db
    svc --> files
    ai -- "prompt + history + files" --> gemini
```

### A mentor chat message

The reply streams token by token over Server-Sent Events; when it finishes, the page saves the
whole conversation.

```mermaid
sequenceDiagram
    actor U as You
    participant C as Mentor page
    participant API as Backend
    participant DB as PostgreSQL
    participant G as Gemini

    U->>C: Type a message (and attach files)
    opt Files attached
        C->>API: POST /api/uploads (one per file)
        API-->>C: {id, filename, url}
    end
    C->>API: POST /api/ai/chat/stream {message, history, attachments}
    API->>DB: Read your profile (name, skills, goals, career, projects)
    API->>DB: Look up the attached files (bytes from backend/uploads/)
    API->>G: System prompt + profile + recent history + files
    loop While Gemini writes
        G-->>API: Text chunk
        API-->>C: data: {"token": "..."}
        C-->>U: Text appears
    end
    API-->>C: data: [DONE]
    C->>API: PUT /api/conversations/{id} (title + all messages)
    API->>DB: Replace the chat's messages
```

### Data and security

- **PostgreSQL** holds everything: users, sessions, skills, user skills, learning goals and
  progress, career goals, projects (incl. write-up HTML), upload metadata, conversations and
  messages. Deletes cascade to everything a row owns.
- **`backend/uploads/`** holds the uploaded files themselves. Nothing is kept in browser storage.
- **Passwords** are hashed with scrypt. A login is a random token in an **httpOnly cookie**;
  the database stores only its SHA-256. A password reset code is 6 random digits, stored only
  as its SHA-256, valid once for `RESET_CODE_MINUTES` and deleted after `RESET_CODE_ATTEMPTS`
  wrong tries. Resetting ends every other login of the account.
- **Sent to Gemini** per reply: your message, recent chat history with its files, and a text
  summary of your profile.

### Project structure

```
backend/
├── main.py                 # Dev entry point: uv run main.py
├── alembic/versions/       # Migrations
├── tests/                  # pytest (separate test database)
└── app/
    ├── main.py             # FastAPI app, routers, CORS, startup report, MCP mount
    ├── config.py           # Settings from .env
    ├── models.py / schemas.py
    ├── dependencies.py     # get_current_user_id() from the session cookie
    ├── security.py         # scrypt hashing, login tokens
    ├── mailer.py           # SMTP emails (password reset codes); printed to the terminal without SMTP_HOST
    ├── manage.py           # CLI: list-users, set-login
    ├── startup_report.py   # ✓ / ✗ startup lines
    ├── mcp_server.py       # MCP tools: ask_mentor, ping
    ├── ai/                 # Gemini client, prompts, profile context, page assistant, resume parsing
    ├── routers/ → services/ → repositories/
frontend/
├── vite.config.js          # /api proxy to the backend
├── vercel.json             # Production rewrites
└── src/
    ├── pages/              # Dashboard, Skills, LearningGoals, CareerGoals, Projects, ProjectDetail, MentorChat
    ├── components/         # PageAssistant, RichEditor, ResumeImportModal, mentor/ (chat UI), ...
    ├── hooks/              # useResource (CRUD), useMe (name, theme)
    └── services/           # api.js, mentorChat.js, sse.js, uploads.js, chats.js
```

---

## API reference

Everything except `/api/auth/*` requires a login. Full interactive docs at `/docs`.

| Resource | Endpoints |
|---|---|
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password` |
| Current user | `GET/PATCH /api/me` (name, theme) |
| Skills | `GET/POST /api/skills`, `GET/PATCH/DELETE /api/skills/{id}` |
| User skills | `GET/POST /api/user-skills`, `GET/PATCH/DELETE /api/user-skills/{id}` |
| Learning goals | `GET/POST /api/learning-goals`, `GET/PATCH/DELETE /api/learning-goals/{id}` |
| Learning progress | `GET/POST /api/learning-goals/{goal_id}/progress`, `GET/PATCH/DELETE .../progress/{id}` |
| Career goals | `GET/POST /api/career-goals`, `GET/PATCH/DELETE /api/career-goals/{id}` |
| Projects | `GET/POST /api/projects`, `GET/PATCH/DELETE /api/projects/{id}` |
| Dashboard | `GET /api/dashboard` |
| AI chat | `POST /api/ai/chat`, `POST /api/ai/chat/stream` (SSE), `GET /api/ai/tip` (`?refresh=true` for a new one) |
| Page assistant | `POST /api/ai/assistant` (`{page, message, history}` → `{reply, actions, changed}`) |
| Conversations | `GET /api/conversations`, `GET/PUT/PATCH/DELETE /api/conversations/{id}` |
| Resume import | `POST /api/resume/parse` (preview, saves nothing), `POST /api/resume/import` |
| Uploads | `POST /api/uploads` (multipart), `GET/DELETE /api/uploads/{id}` |
| MCP | `/mcp` (Streamable HTTP, `Authorization: Bearer <MCP_TOKEN>`) |

**Status codes:** `201` created, `204` deleted, `401` not logged in, `404` not found (or not
yours), `409` duplicate, `422` invalid input.

**Enum values:**

| Field | Values |
|---|---|
| Learning goal status | `active`, `paused`, `completed`, `abandoned` |
| Career goal status | `active`, `paused`, `achieved`, `abandoned` |
| Project status | `planned`, `in_progress`, `completed`, `on_hold` |
| User skill status | `want_to_learn`, `learning`, `acquired` |
| User skill proficiency | `beginner`, `intermediate`, `advanced`, `expert` |

---

## AI mentor

- **Personalised:** each reply includes your name, skills, goals (with latest progress), career
  roles and projects (`ai/context.py`, max 20 per list). Still answers if the database is down.
- **Attachments:** up to 5 images, PDFs or text/code files per message. Types are checked from
  content; SVG, Word and video are rejected.
- **Page assistant tools** (`ai/assistant.py`, e.g. `set_skill`, `log_progress`, `update_project`)
  go through the normal services, so the same validation applies.
- **Resume import** finds skills and projects in a PDF, image or text resume; you choose what to save.

**Free tier:** about 20 requests per day per model. When the quota runs out the chat says when it
resets; switch `GEMINI_MODEL` (e.g. `gemini-3.5-flash-lite`, which has its own limit) or enable billing.

**Errors are never faked**; they appear in the reply bubble:

| Problem | `POST /api/ai/chat` | `POST /api/ai/chat/stream` |
|---|---|---|
| Key missing/rejected, model not found | `503` | `data: {"error": "..."}` |
| Rate limit / quota | `429` | `data: {"error": "..."}` |
| Gemini down or timeout (after 3 tries) | `503` / `504` | `data: {"error": "..."}` |
| Attached file no longer exists | `400` | `400` |
| Stream cut off midway | | tokens so far, then `data: {"error": "..."}` |

---

## Development

Run from `backend/` unless noted.

| Task | Command |
|---|---|
| Run tests | `uv run pytest` (needs `mentora-postgres` running) |
| Add a dependency | `uv add <package>` |
| Apply migrations | `uv run alembic upgrade head` |
| Create a migration | `uv run alembic revision --autogenerate -m "describe change"` |
| List accounts | `uv run python -m app.manage list-users` |
| Set an account's login | `uv run python -m app.manage set-login --user-id 1 --email you@example.com` |
| Open the database | `docker exec -it mentora-postgres psql -U mentora -d mentora` |
| Build the frontend | `npm run build` (in `frontend/`) |

---

## Roadmap

- Email verification
- Automated frontend tests; backend tests for career goals and projects CRUD
