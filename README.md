# Mentora AI

AI-powered Personal Learning and Career Intelligence Companion.

Mentora AI helps you track the skills you're learning, your learning goals and
progress, your career goals and your projects, and gives you an AI mentor to chat with.

---

## Tech stack

| Part | Technologies |
|---|---|
| Frontend | React 19 + Vite 8, JavaScript/JSX, Bootstrap 5 (dark theme) + Bootstrap Icons, React Router 7, react-markdown, TipTap (rich-text editor) |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic |
| Database | PostgreSQL 16 (runs in Docker for local development) |
| AI | Google Gemini (`google-genai` SDK): streaming (SSE), file attachments, automatic retries; MCP server for AI tools |
| Tests | pytest + httpx (backend); Playwright browser checks during development |

---

## Project structure

```
mentora-ai/
├── README.md
├── backend/
│   ├── .env                    # DATABASE_URL, GEMINI_API_KEY, ... (not committed)
│   ├── .env.example            # Template for .env
│   ├── pyproject.toml          # Dependencies + pytest settings (uv)
│   ├── uv.lock                 # Exact dependency versions
│   ├── requirements.txt        # Same packages, for pip
│   ├── main.py                 # Dev entry point: uv run main.py
│   ├── alembic.ini
│   ├── alembic/versions/       # Database migrations
│   ├── tests/                  # pytest tests (use a separate test database)
│   ├── uploads/                # Uploaded files (not committed)
│   └── app/
│       ├── main.py             # FastAPI app, routers, CORS, startup (report + MCP)
│       ├── config.py           # Settings from .env
│       ├── database.py         # Engine, sessions, get_db()
│       ├── models.py           # SQLAlchemy models (10 tables)
│       ├── schemas.py          # Pydantic Create / Update / Response schemas
│       ├── dependencies.py     # get_current_user_id(): the logged-in user, from the session cookie
│       ├── security.py         # Password hashing (scrypt) and login tokens
│       ├── manage.py           # Account commands: list-users, set-login
│       ├── startup_report.py   # The ✓ / ✗ lines printed when the backend starts
│       ├── mcp_server.py       # MCP server (tools: ask_mentor, ping)
│       ├── ai/                 # Mentor: Gemini client, prompts, user profile, attachments, resume reading
│       ├── routers/            # HTTP endpoints
│       ├── services/           # Business rules (404 / 409 checks, ownership)
│       └── repositories/       # Database queries
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx             # Routes
        ├── main.jsx
        ├── layouts/            # MainLayout (navbar)
        ├── pages/              # Dashboard, Skills, LearningGoals, CareerGoals, Projects,
        │                       # ProjectDetail, MentorChat
        ├── components/         # BotAvatar, ProgressRing, RichEditor, FormModal, Modal,
        │                       # ResumeImportModal, PageAssistant (floating bot), ...
        │   └── mentor/         # Chat: MentorHome, ChatSidebar, ChatMessage, Composer
        ├── hooks/              # useResource (load / create / update / delete), useMe (name, theme)
        ├── services/           # api.js, mentorChat.js, sse.js, uploads.js, chats.js
        └── utils/              # format.js
```

The backend follows a layered design: **router → service → repository → database**.

---

## How it works

Two [Mermaid](https://mermaid.js.org/) diagrams (GitHub and VS Code's Markdown preview draw them):
the overall flow, and the sequence of one mentor chat message.

### Flow: architecture

```mermaid
flowchart TB
    user(["You (browser)"])

    subgraph FE["Frontend: React + Vite (localhost:5173)"]
        direction LR
        pages["Pages<br/>Dashboard, Skills, Goals,<br/>Career, Projects, Mentor"] --> services["services/<br/>api.js, chats.js, sse.js, uploads.js"]
    end

    subgraph BE["Backend: FastAPI (127.0.0.1:8002)"]
        direction LR
        routers["routers/<br/>HTTP endpoints"] --> svc["services/<br/>rules, 404 / 409 checks"] --> repos["repositories/<br/>database queries"]
        routers --> ai["ai/<br/>prompts, profile, Gemini client"]
        mcp["MCP server<br/>/mcp"] --> ai
        ai -- "your profile" --> repos
    end

    subgraph EXT["Storage and services"]
        direction LR
        db[("PostgreSQL in Docker<br/>users, skills, goals, projects,<br/>chats, uploads, ...")]
        files[("backend/uploads/<br/>uploaded files")]
        gemini["Google Gemini API"]
    end

    user --> FE
    services -- "JSON over HTTP (chat replies as SSE)" --> routers
    repos --> db
    svc --> files
    ai -- "prompt + history + files" --> gemini
```

Every request goes **router → service → repository → database**. `get_current_user_id()` reads
the login cookie (401 if there is none), and every query is filtered by that user, so each account
only sees its own data.

### Sequence: chatting with the mentor

The reply streams in word by word (Server-Sent Events). When it is finished, the page saves the
whole conversation in the database.

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
    Note over C,DB: Reopening the chat later loads it with GET /api/conversations/{id}
```

If Gemini fails (no key, quota used up, timeout), the stream sends `data: {"error": "..."}`
instead of `[DONE]`, and the error is shown in the reply bubble and saved with the chat.

---

## Getting started

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/) (or pip)
- Node.js 20.19+ and npm
- Docker (for PostgreSQL)

### 1. Start PostgreSQL (Docker)

First time only:

```bash
docker run -d --name mentora-postgres \
  -e POSTGRES_USER=mentora -e POSTGRES_PASSWORD=YOUR_DB_PASSWORD -e POSTGRES_DB=mentora \
  -p 5432:5432 -v mentora_pgdata:/var/lib/postgresql/data \
  --restart unless-stopped postgres:16
```

Afterwards, if it's stopped:

```bash
docker start mentora-postgres
```

### 2. Backend

The backend uses [uv](https://docs.astral.sh/uv/). Install it once:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

`uv run` creates `backend/.venv` and installs the dependencies from `uv.lock`
automatically the first time, so there is no separate install step.

Prefer pip? `backend/requirements.txt` lists the same packages (only the ones the code
uses, at the tested versions):

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Create `backend/.env` (copy `backend/.env.example`; if you already have a `.env`,
just add the lines you're missing). **Private addresses, passwords and keys live only in the
`.env` files** (git-ignored), never in the code:

```env
# Required: the same password as POSTGRES_PASSWORD above
DATABASE_URL=postgresql+psycopg2://mentora:YOUR_DB_PASSWORD@localhost:5432/mentora
# Optional, these are the defaults: where `uv run main.py` runs the backend
API_HOST=127.0.0.1
API_PORT=8002
# MCP clients send "Authorization: Bearer <MCP_TOKEN>"; the tools act as MCP_USER_ID.
# Make a token: python -c "import secrets; print(secrets.token_urlsafe(32))"
MCP_TOKEN=a-long-random-token
MCP_USER_ID=1

# Required for the AI mentor (see "About the AI mentor" below)
GEMINI_API_KEY=your-key-here
# Optional, defaults to gemini-3.5-flash
GEMINI_MODEL=gemini-3.5-flash
# Optional, defaults to 60
GEMINI_TIMEOUT_SECONDS=60
# Optional: earlier chat messages sent with each new one (0 = none), defaults to 20
CHAT_HISTORY_LIMIT=20
# Optional: max size per uploaded file in MB, defaults to 20
MAX_UPLOAD_MB=20
```

Create the tables and start the server:

```bash
cd backend
uv run alembic upgrade head
uv run main.py          # http://API_HOST:API_PORT, restarts when app/ changes
```

On startup the terminal shows one ✓ / ✗ line per part, so you can see what works:

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

A ✗ line says what's wrong and how to fix it (e.g. `docker start mentora-postgres`). Each MCP
tool call also prints a line: `MCP ▶ ask_mentor called`, then `MCP ✓ ask_mentor done in 1.2s`
(or `MCP ✗ ... failed`).
Change the name with the ✏️ next to the Dashboard greeting (or `PATCH /api/me`); the app
and the mentor then greet you by it.

- API docs (Swagger): http://127.0.0.1:8002/docs
- MCP endpoint: http://127.0.0.1:8002/mcp

### 3. Frontend

```bash
cd frontend
npm install
```

The frontend has no `.env` of its own: the dev server reads `API_HOST` and `API_PORT` from
`backend/.env` and forwards `/api` on localhost:5173 to the backend, so the login cookie works.
Nothing from `backend/.env` is sent to the browser.

```bash
npm run dev
```

Open http://localhost:5173 (the backend's CORS only allows port 5173).

---

## Features

### Accounts and logins

- **Sign up / Log in** pages (email + password); anyone can create an account, and each account
  has its own skills, goals, career roles, projects and chats. **Log out** is in the navbar.
- Passwords are hashed with **scrypt** (Python standard library); the plain password is never stored.
- The login is a random token in an **httpOnly cookie** (JavaScript can't read it), valid
  `SESSION_DAYS` (30) days; the database keeps only its SHA-256. Log out deletes the session.
- An account from before logins existed gets an email and password with
  `uv run python -m app.manage set-login --user-id 1 --email you@example.com` (asks for the password).

### Frontend pages

| Page | URL | What it does |
|---|---|---|
| Dashboard | `/` | Greeting by name, counts per page, learning-goal progress bars, AI tip of the day |
| Skills | `/skills` | Table with your **level** and **status** per skill (change in place), filters, add/edit/delete; **Import from resume** |
| Learning Goals | `/goals` | Cards with a progress ring; **Update progress** (slider, note, history, mark completed) |
| Career Goals | `/career` | Target roles with needed skills; readiness ring; add/remove skills in place; ask for a roadmap |
| Projects | `/projects` | Cards (cover image from the write-up); **Import from resume**; `/projects/:id` has a rich-text write-up with images |
| AI Mentor | `/mentor` | ChatGPT-style chat: streaming replies, chat list, rename, edit messages, file uploads |

The Skills, Goals, Career and Projects pages have a **floating Mentora bot** (bottom right): ask it in
plain words ("set Docker to advanced", "I'm 60% done with my RAG goal") and it changes that page's
data, then the page refreshes. It asks before deleting anything.

The whole app is dark by default (sun/moon button in the navbar for light), and works on phones.

### Backend API

Everything except `/api/auth/*` needs a login (else **401**). The user comes from the login
cookie, never from the request, and another user's data always returns **404**.

| Resource | Endpoints |
|---|---|
| Accounts | `POST /api/auth/register` (`{full_name, email, password}`), `POST /api/auth/login`, `POST /api/auth/logout` |
| Skills (per user) | `GET/POST /api/skills`, `GET/PATCH/DELETE /api/skills/{id}` |
| Learning goals | `GET/POST /api/learning-goals`, `GET/PATCH/DELETE /api/learning-goals/{id}` |
| Learning progress | `GET/POST /api/learning-goals/{goal_id}/progress`, `GET/PATCH/DELETE .../progress/{id}` |
| User skills | `GET/POST /api/user-skills`, `GET/PATCH/DELETE /api/user-skills/{id}` |
| Career goals | `GET/POST /api/career-goals`, `GET/PATCH/DELETE /api/career-goals/{id}` |
| Projects | `GET/POST /api/projects`, `GET/PATCH/DELETE /api/projects/{id}` |
| Current user | `GET/PATCH /api/me` (name, theme) |
| Page assistant | `POST /api/ai/assistant` (`{page, message, history}` → `{reply, actions, changed}`; Gemini calls tools that change the page's data) |
| AI chat | `POST /api/ai/chat`, `POST /api/ai/chat/stream` (Server-Sent Events), `GET /api/ai/tip` (saved for the day; `?refresh=true` for a new one) |
| Mentor chats | `GET /api/conversations`, `GET/PUT/PATCH/DELETE /api/conversations/{id}` (`PUT` saves the whole chat) |
| Resume import | `POST /api/resume/parse` (`{upload_id}` → skills and projects found; saves nothing), `POST /api/resume/import` (saves the ones you picked) |
| Dashboard | `GET /api/dashboard` (counts per page + learning-goal progress) |
| Uploads | `POST /api/uploads` (multipart), `GET` / `DELETE /api/uploads/{id}`: images, PDFs, text/code, max `MAX_UPLOAD_MB` |
| MCP | `/mcp` (Streamable HTTP; tools `ask_mentor`, `ping`); needs `Authorization: Bearer <MCP_TOKEN>` |

Status codes: `201` created, `204` deleted, `404` not found, `409` duplicate
(skill name, or a skill the user already has), `422` invalid input.

Allowed status values:

| Field | Values |
|---|---|
| Learning goal status | `active`, `paused`, `completed`, `abandoned` |
| Career goal status | `active`, `paused`, `achieved`, `abandoned` |
| Project status | `planned`, `in_progress`, `completed`, `on_hold` |
| User skill status | `want_to_learn`, `learning`, `acquired` |
| User skill proficiency | `beginner`, `intermediate`, `advanced`, `expert` |

### Database tables

`users` (incl. `password_hash`, `theme` and today's tip), `sessions` (logins), `skills` (per user), `user_skills`, `learning_goals`, `learning_progress`,
`career_goals` (incl. `required_skills`), `projects` (incl. `content`, the write-up HTML),
`uploads` (file details; the files are in `backend/uploads/`), `conversations` and
`chat_messages` (mentor chats). Deleting a user (or a goal or
skill) also deletes everything that belongs to it (`ON DELETE CASCADE`).

### Where the data is stored

| Where | What |
|---|---|
| PostgreSQL in Docker (`mentora-postgres`, volume `mentora_pgdata`) | Everything: your name and theme, skills, goals, progress, career goals, projects, mentor chats, today's tip, upload details |
| `backend/uploads/` (git-ignored) | The uploaded files themselves (chat attachments, project images) |
| `backend/.env` (git-ignored) | Database URL, Gemini API key and model |

Nothing is kept in the browser (no localStorage).

Sent to Google Gemini for each reply: your message, the recent chat history with its files,
and a text summary of your profile (skills, goals, career roles, projects).

---

## About the AI mentor

Replies come from **Google Gemini** (`google-genai` SDK, `backend/app/ai/llm_client.py`).

- **Knows your data:** each reply includes your name, skills, goals (with latest progress), career
  roles and projects (`ai/context.py`, max 20 per list). If the database is down it still answers.
- **Chats like ChatGPT:** streaming Markdown replies, chat list, follow-ups (newest
  `CHAT_HISTORY_LIMIT` = 20 messages sent), edit a sent message, rename chats. Saved in the database.
- **Files:** attach up to 5 images, PDFs or code/text files per message (`MAX_UPLOAD_MB` each).
  The type is checked from the content; SVG, Word and video are rejected.
- **Page assistant:** on Skills, Goals, Career and Projects, Gemini gets *tools* for that page only
  (`ai/assistant.py`, e.g. `set_skill`, `log_progress`, `update_project`). Each tool goes through the
  normal services, so the same checks apply; deletes need your confirmation first.
- **Greets you by name**, and **Import from resume** (Skills / Projects pages) finds your skills
  and projects in a PDF, image or text resume; you pick what to save.

**Setup:** create a key at [Google AI Studio](https://aistudio.google.com/apikey), put
`GEMINI_API_KEY=...` in `backend/.env` and restart the backend. Only the backend reads the key;
never put it in frontend code. Change models with
`GEMINI_MODEL`, no code changes needed.

**Free tier:** about **20 requests per day per model** (chat messages and tips). When it runs out
the chat says when it resets; switch `GEMINI_MODEL` (e.g. `gemini-3.5-flash-lite`) or enable billing.

**When Gemini fails** there is no fake answer; the error is shown in the reply bubble:

| Problem | `POST /api/ai/chat` | `POST /api/ai/chat/stream` |
|---|---|---|
| Key missing or rejected, model not found | `503` | `data: {"error": "..."}` |
| Rate limit / quota | `429` | `data: {"error": "..."}` |
| Gemini down, timeout (after 3 tries) | `503` / `504` | `data: {"error": "..."}` |
| Attached file no longer exists | `400` | `400` |
| Stream cut off midway | | tokens so far, then `data: {"error": "..."}` (no `[DONE]`) |

---

## Tests


```bash
cd backend
docker start mentora-postgres   # if it's not running
uv run pytest                   # add -v for each test name
```


---

## Useful commands

| Task | Command (run inside `backend/`) |
|---|---|
| Add a Python dependency | `uv add <package>` (updates `pyproject.toml` and `uv.lock`) |
| List accounts | `uv run python -m app.manage list-users` |
| Give an account an email + password | `uv run python -m app.manage set-login --user-id 1 --email you@example.com` |
| Apply migrations | `uv run alembic upgrade head` |
| Create a migration after changing models | `uv run alembic revision --autogenerate -m "describe change"` |
| Open the database | `docker exec -it mentora-postgres psql -U mentora -d mentora` |
| Build the frontend (in `frontend/`) | `npm run build` |

---

## Not built yet

- Password reset by email, and email verification (accounts are email + password only)
- Automated frontend tests; dedicated backend tests for career goals and projects CRUD
