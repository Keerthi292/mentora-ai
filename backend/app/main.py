import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.mcp_server import mcp, mcp_app
from app.routers import ai as ai_router
from app.routers import career_goals as career_goals_router
from app.routers import conversations as conversations_router
from app.routers import dashboard as dashboard_router
from app.routers import learning_goals as learning_goals_router
from app.routers import learning_progress as learning_progress_router
from app.routers import me as me_router
from app.routers import projects as projects_router
from app.routers import resume as resume_router
from app.routers import skills as skills_router
from app.routers import uploads as uploads_router
from app.routers import user_skills as user_skills_router
from app.seed import run_seed

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) Make sure the demo user exists (no authentication yet).
    #    If the database is down, log it and keep starting, so /api/ai/* and
    #    /mcp still work; database endpoints will fail until it's back.
    try:
        run_seed()
    except Exception:
        logger.exception("Could not seed the demo user. Is PostgreSQL running?")

    # 2) The MCP session manager must run while the app is running
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="Mentora AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router.router)
app.include_router(me_router.router)
app.include_router(conversations_router.router)
app.include_router(skills_router.router)
app.include_router(learning_goals_router.router)
app.include_router(user_skills_router.router)
app.include_router(learning_progress_router.router)
app.include_router(career_goals_router.router)
app.include_router(projects_router.router)
app.include_router(dashboard_router.router)
app.include_router(uploads_router.router)
app.include_router(resume_router.router)


@app.get("/")
def root():
    return {"message": "Mentora AI backend is running"}


# Mount LAST, at "/": the MCP app serves /mcp, and your own routes above win first
app.mount("/", mcp_app)