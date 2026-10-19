import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
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
from app.startup_report import print_startup_report, setup_logging

setup_logging()  # show the app's log lines (startup report, MCP tool calls) in the terminal
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) Make sure the demo user exists (no authentication yet).
    #    If the database is down, log it and keep starting, so /api/ai/* and
    #    /mcp still work; database endpoints will fail until it's back.
    try:
        run_seed()
    except Exception as exc:
        # One line only: the startup report below explains the database problem
        logger.warning("Could not create the demo user: %s", str(exc).splitlines()[0])

    # 2) The MCP session manager must run while the app is running
    async with mcp.session_manager.run():
        # 3) One ✓/✗ line per part (database, migrations, Gemini, MCP, ...)
        try:
            print_startup_report(engine, [tool.name for tool in await mcp.list_tools()])
        except Exception:
            logger.exception("Could not print the startup report")
        yield


app = FastAPI(title="Mentora AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # CORS_ORIGINS in backend/.env
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