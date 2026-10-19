import functools
import logging
import time

from mcp.server.fastmcp import FastMCP

from app.ai.agent import get_mentor_response
from app.ai.context import build_user_profile
from app.ai.schemas import ChatRequest
from app.database import SessionLocal
from app.dependencies import get_current_user_id

logger = logging.getLogger(__name__)

# stateless_http + json_response keeps Streamable HTTP simple for a first version.
# log_level: FastMCP sets up logging for every library; only show their warnings
# (the app's own lines, like the startup report, are set up in app/startup_report.py)
mcp = FastMCP("Mentora AI", stateless_http=True, json_response=True, log_level="WARNING")


def logged(tool):
    """Print a terminal line when an MCP tool runs, and whether it worked."""

    @functools.wraps(tool)
    def wrapper(*args, **kwargs):
        logger.info("MCP ▶ %s called", tool.__name__)
        start = time.perf_counter()
        try:
            result = tool(*args, **kwargs)
        except Exception as exc:
            logger.warning("MCP ✗ %s failed after %.1fs: %s", tool.__name__, time.perf_counter() - start, exc)
            raise
        logger.info("MCP ✓ %s done in %.1fs", tool.__name__, time.perf_counter() - start)
        return result

    return wrapper


@mcp.tool()
@logged
def ask_mentor(message: str) -> str:
    """Ask the Mentora AI mentor a learning or career question."""
    request = ChatRequest(message=message)
    with SessionLocal() as db:
        profile = build_user_profile(db, get_current_user_id())
    return get_mentor_response(request, profile).response


@mcp.tool()
@logged
def ping() -> str:
    """Check that the Mentora AI MCP server is alive."""
    return "Mentora AI MCP server is running"


# Build the ASGI app now so mcp.session_manager exists for main.py's lifespan
mcp_app = mcp.streamable_http_app()