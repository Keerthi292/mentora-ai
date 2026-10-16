# Mentora AI

AI-powered Personal Learning and Career Intelligence Companion.

Mentora AI helps you track the skills you're learning, your learning goals and
progress, your career goals and your projects, and gives you an AI mentor to chat with.

> **Status:** early development. The app runs end to end with a **single demo user**
> (no login yet) and an AI mentor powered by **Google Gemini**.
> See [PROGRESS.md](PROGRESS.md) for everything done so far.

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
├── PROGRESS.md                 # What has been built so far
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
│       ├── main.py             # FastAPI app, routers, CORS, startup (seed + MCP)
│       ├── config.py           # Settings from .env
│       ├── database.py         # Engine, sessions, get_db()
│       ├── models.py           # SQLAlchemy models (8 tables)
│       ├── schemas.py          # Pydantic Create / Update / Response schemas
│       ├── dependencies.py     # get_current_user_id() -> demo user
│       ├── seed.py             # Creates the demo user
│       ├── mcp_server.py       # MCP server (tools: ask_mentor, ping)
│       ├── ai/                 # Mentor: Gemini client, prompts, user profile, attachments
│       ├── routers/            # HTTP endpoints
│       ├── services/           # Business rules (404 / 409 checks, ownership)
│       └── repositories/       # Database queries
└── frontend/
    ├── .env                    # VITE_API_BASE_URL (not committed)
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx             # Routes
        ├── main.jsx
        ├── layouts/            # MainLayout (navbar)
        ├── pages/              # Dashboard, Skills, LearningGoals, CareerGoals, Projects,
        │                       # ProjectDetail, MentorChat
        ├── components/         # BotAvatar, ProgressRing, RichEditor, FormModal, Modal, ...
        │   └── mentor/         # Chat: MentorHome, ChatSidebar, ChatMessage, Composer
        ├── hooks/              # useResource (load / create / update / delete)
        ├── services/           # api.js, mentorChat.js, sse.js, uploads.js, chatStorage.js
        └── utils/              # format.js
```

The backend follows a layered design: **router → service → repository → database**.

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
  -e POSTGRES_USER=mentora -e POSTGRES_PASSWORD=mentora_dev -e POSTGRES_DB=mentora \
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
just add the lines you're missing):

```env
DATABASE_URL=postgresql+psycopg2://mentora:mentora_dev@localhost:5432/mentora
# Optional, defaults to 1
DEMO_USER_ID=1

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
uv run main.py          # http://127.0.0.1:8002, restarts when app/ changes
```

On startup the demo user (`Demo User`, `demo@mentora.local`) is created automatically.

- API docs (Swagger): http://127.0.0.1:8002/docs
- MCP endpoint: http://127.0.0.1:8002/mcp

### 3. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8002
```

```bash
npm run dev
```

Open http://localhost:5173 (the backend's CORS only allows port 5173).

---

## Features

### Frontend pages

| Page | URL | What it does |
|---|---|---|
| Dashboard | `/` | Greeting, counts per page, learning-goal progress bars, AI tip of the day |
| Skills | `/skills` | Table: add, edit, delete skills |
| Learning Goals | `/goals` | Cards with a progress ring; **Update progress** (slider, note, history, mark completed) |
| Career Goals | `/career` | Target roles with needed skills; readiness ring; add/remove skills in place; ask for a roadmap |
| Projects | `/projects` | Cards (cover image from the write-up); `/projects/:id` has a rich-text write-up with images |
| AI Mentor | `/mentor` | ChatGPT-style chat: streaming replies, chat list, rename, edit messages, file uploads |

The whole app is dark by default (sun/moon button in the navbar for light), and works on phones.

### Backend API

All user data belongs to the demo user (no `user_id` is sent by the client).
Another user's data always returns **404**.

| Resource | Endpoints |
|---|---|
| Skills (shared catalog) | `GET/POST /api/skills`, `GET/PATCH/DELETE /api/skills/{id}` |
| Learning goals | `GET/POST /api/learning-goals`, `GET/PATCH/DELETE /api/learning-goals/{id}` |
| Learning progress | `GET/POST /api/learning-goals/{goal_id}/progress`, `GET/PATCH/DELETE .../progress/{id}` |
| User skills | `GET/POST /api/user-skills`, `GET/PATCH/DELETE /api/user-skills/{id}` |
| Career goals | `GET/POST /api/career-goals`, `GET/PATCH/DELETE /api/career-goals/{id}` |
| Projects | `GET/POST /api/projects`, `GET/PATCH/DELETE /api/projects/{id}` |
| AI chat | `POST /api/ai/chat`, `POST /api/ai/chat/stream` (Server-Sent Events), `GET /api/ai/tip` |
| Dashboard | `GET /api/dashboard` (counts per page + learning-goal progress) |
| Uploads | `POST /api/uploads` (multipart), `GET` / `DELETE /api/uploads/{id}`: images, PDFs, text/code, max `MAX_UPLOAD_MB` |
| MCP | `/mcp` (Streamable HTTP; tools `ask_mentor`, `ping`) |

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

`users`, `skills`, `user_skills`, `learning_goals`, `learning_progress`,
`career_goals` (incl. `required_skills`), `projects` (incl. `content`, the write-up HTML),
`uploads` (file details; the files are in `backend/uploads/`). Deleting a user (or a goal or
skill) also deletes everything that belongs to it (`ON DELETE CASCADE`).

### Where the data is stored

| Where | What |
|---|---|
| PostgreSQL in Docker (`mentora-postgres`, volume `mentora_pgdata`) | Skills, goals, progress, career goals, projects, upload details |
| `backend/uploads/` (git-ignored) | The uploaded files themselves (chat attachments, project images) |
| Browser localStorage | Mentor chats (`mentora.conversations.v1`), today's tip, theme. Per browser. |
| `backend/.env` (git-ignored) | Database URL, Gemini API key and model |

Sent to Google Gemini for each reply: your message, the recent chat history with its files,
and a text summary of your profile (skills, goals, career roles, projects).

---

## About the AI mentor

Replies come from **Google Gemini**, called from `backend/app/ai/llm_client.py`
with the official Google Gen AI SDK (`google-genai`). The streaming endpoint
forwards Gemini's text chunks as they arrive.

**It knows your data.** Before each reply, `backend/app/ai/context.py` reads what you
saved on the Skills, Learning Goals (with the latest progress update), Career Goals and
Projects pages and adds it to the prompt, so the mentor answers for *you*. Add or edit
something on those pages and the next message already uses it. Each list is capped at
20 items and long descriptions are shortened, to keep requests fast and cheap. If the
database can't be read, the mentor still answers, just without your profile.

**The Mentor page** opens on a landing screen (animated robot, quick-start ideas); **Start a
new chat** or a suggestion card opens the chat. Replies render as Markdown with a copy button,
and the robot jitters while it thinks. The whole app is dark by default; the sun/moon button
in the navbar switches to light (remembered per browser).

**It remembers the conversation.** The chat page works like ChatGPT: a list of your
chats on the left (grouped Today / Yesterday / ...), **+ New chat**, and a delete button
per chat. Each new message is sent with the earlier messages of that chat, so follow-ups
like "explain the second point" work. Only the newest `CHAT_HISTORY_LIMIT` messages
(default 20) are sent to Gemini. Chats are saved in your browser (localStorage), not in
the database: they survive a reload but aren't shared across browsers or devices.

**Edit and rename.** Hover over a message you sent and click **Edit**: the replies after it are
replaced and the mentor answers the edited text. The ✏️ next to a chat in the sidebar renames it.

**Images and files.** The **+** button next to the message box (also on the landing screen)
uploads images (PNG, JPEG, WebP, GIF) or files (PDF, code, text, CSV, JSON); you can also drop
or paste them. Up to 5 per message, `MAX_UPLOAD_MB` (20) each. Gemini reads them, and still sees
them in follow-up questions. The file type is checked from the content, not the name, and SVG,
Word and video files are rejected.

**Get an API key**

1. Open [Google AI Studio](https://aistudio.google.com/apikey) and sign in with a Google account.
2. Click **Create API key** (pick or create a Google Cloud project when asked).
3. Copy the key into `backend/.env` as `GEMINI_API_KEY=...` and restart the backend.

The key is only read by the backend. It is never sent to the frontend, returned by
the API, or logged, and `backend/.env` is in `.gitignore`. Never put it in
`frontend/.env`: anything `VITE_*` ends up in the browser.

**Change the model** with `GEMINI_MODEL` in `backend/.env` (see the
[model list](https://ai.google.dev/gemini-api/docs/models)); no code changes needed.

**Free-tier limits:** a free API key allows only about **20 requests per day per model**
(every chat message and dashboard tip counts). When it runs out, the chat says so and when it
resets. To keep going, switch `GEMINI_MODEL` (each model has its own daily limit, e.g.
`gemini-3.5-flash-lite`) or enable billing in Google AI Studio. Usage: https://ai.dev/rate-limit

**When Gemini fails** there is no fake answer:

| Problem | `POST /api/ai/chat` | `POST /api/ai/chat/stream` |
|---|---|---|
| `GEMINI_API_KEY` missing, key rejected, model not found | `503` | `data: {"error": "..."}` |
| Rate limit / quota | `429` | `data: {"error": "..."}` |
| Gemini down, timeout, network error (after 3 automatic tries) | `503` / `504` | `data: {"error": "..."}` |
| A file attached to the message no longer exists | `400` | `400` |
| Stream cut off midway | | tokens so far, then `data: {"error": "..."}` (no `[DONE]`) |

The chat page shows the error message in the reply bubble.

---

## Tests

Backend tests run against a separate PostgreSQL database (`mentora_test`, created
automatically), so your development data is never touched.

```bash
cd backend
docker start mentora-postgres   # if it's not running
uv run pytest                   # add -v for each test name
```

Current result: **130 passed** (AI chat, attachments, retries, dashboard, uploads, skills,
learning goals, demo user).
Gemini is replaced by a fake in tests, so they need no API key and use no quota.

---

## Useful commands

| Task | Command (run inside `backend/`) |
|---|---|
| Add a Python dependency | `uv add <package>` (updates `pyproject.toml` and `uv.lock`) |
| Create the demo user manually | `uv run python -m app.seed` |
| Apply migrations | `uv run alembic upgrade head` |
| Create a migration after changing models | `uv run alembic revision --autogenerate -m "describe change"` |
| Open the database | `docker exec -it mentora-postgres psql -U mentora -d mentora` |
| Build the frontend (in `frontend/`) | `npm run build` |

---

## Not built yet

- Authentication (the app uses one demo user on purpose for now)
- Chat history saved on the server (it's per browser for now)
- UI for skill levels (`user_skills`: proficiency per skill; the API exists)
- Automated frontend tests; dedicated backend tests for career goals and projects CRUD
