# Mentora AI

AI-powered Personal Learning and Career Intelligence Companion.

Mentora AI helps you track the skills you're learning, your learning goals and
progress, your career goals and your projects, and gives you an AI mentor to chat with.

> **Status:** early development. The app runs end to end with a **single demo user**
> (no login yet) and a **mock AI** (no real LLM connected yet).
> See [PROGRESS.md](PROGRESS.md) for everything done so far.

---

## Tech stack

| Part | Technologies |
|---|---|
| Frontend | React 19 + Vite 8, JavaScript/JSX, Bootstrap 5, React Router 7 |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic |
| Database | PostgreSQL 16 (runs in Docker for local development) |
| AI | Mock LLM (placeholder) with streaming (SSE); MCP server for AI tools |
| Tests | pytest + httpx (backend) |

---

## Project structure

```
mentora-ai/
├── README.md
├── PROGRESS.md                 # What has been built so far
├── backend/
│   ├── .env                    # DATABASE_URL, DEMO_USER_ID (not committed)
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/versions/       # Database migrations
│   ├── pytest.ini
│   ├── tests/                  # pytest tests (use a separate test database)
│   └── app/
│       ├── main.py             # FastAPI app, routers, CORS, startup (seed + MCP)
│       ├── config.py           # Settings from .env
│       ├── database.py         # Engine, sessions, get_db()
│       ├── models.py           # SQLAlchemy models (7 tables)
│       ├── schemas.py          # Pydantic Create / Update / Response schemas
│       ├── dependencies.py     # get_current_user_id() -> demo user
│       ├── seed.py             # Creates the demo user
│       ├── mcp_server.py       # MCP server (tools: ask_mentor, ping)
│       ├── ai/                 # Mentor logic, prompts, mock LLM client
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
        ├── pages/              # Dashboard, Skills, LearningGoals, CareerGoals, Projects, MentorChat
        ├── components/         # CrudPage, FormModal, Modal, ConfirmDeleteModal, StatusBadge
        ├── hooks/              # useResource (load / create / update / delete)
        ├── services/           # api.js, mentorChat.js, sse.js
        └── utils/              # format.js
```

The backend follows a layered design: **router → service → repository → database**.

---

## Getting started

### Prerequisites

- Python 3.13+ (3.11+ should work)
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

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://mentora:mentora_dev@localhost:5432/mentora
# Optional, defaults to 1
DEMO_USER_ID=1
```

Create the tables and start the server:

```bash
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8002
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
| Dashboard | `/` | Placeholder; shows whether the backend is online |
| Skills | `/skills` | List, add, edit, delete skills |
| Learning Goals | `/goals` | List, add, edit, delete learning goals (status, target date) |
| Career Goals | `/career` | List, add, edit, delete career goals |
| Projects | `/projects` | List, add, edit, delete projects (technologies, status) |
| AI Mentor | `/mentor` | Chat with the mentor; replies stream in word by word |

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
| AI chat | `POST /api/ai/chat`, `POST /api/ai/chat/stream` (Server-Sent Events) |
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
`career_goals`, `projects`. Deleting a user (or a goal or skill) also deletes
everything that belongs to it (`ON DELETE CASCADE`).

---

## About the AI mentor

**No real LLM is connected yet.** Replies come from a placeholder in
`backend/app/ai/llm_client.py`, which returns:

> Mentora AI (mock response): I received your message: "...". Real, personalized
> guidance will be available once an LLM is connected.

It streams the sentence one word at a time to imitate a real model. To connect a
real model (e.g. Claude), only `llm_client.py` needs to change.

---

## Tests

Backend tests run against a separate PostgreSQL database (`mentora_test`, created
automatically), so your development data is never touched.

```bash
cd backend
docker start mentora-postgres   # if it's not running
.venv/bin/pytest                # add -v for each test name
```

Current result: **50 passed** (AI chat, skills, learning goals, demo user).

---

## Useful commands

| Task | Command (run inside `backend/`) |
|---|---|
| Create the demo user manually | `.venv/bin/python -m app.seed` |
| Apply migrations | `.venv/bin/alembic upgrade head` |
| Create a migration after changing models | `.venv/bin/alembic revision --autogenerate -m "describe change"` |
| Open the database | `docker exec -it mentora-postgres psql -U mentora -d mentora` |
| Build the frontend (in `frontend/`) | `npm run build` |

---

## Not built yet

- Authentication (the app uses one demo user on purpose for now)
- A real LLM behind the mentor, conversation memory, and personalized advice
- Dashboard content
- UI for user skills and learning progress (the APIs exist)
- Frontend tests; backend pytest tests for user skills, progress, career goals and projects
