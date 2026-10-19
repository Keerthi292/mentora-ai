import functools
import hmac
import json
import logging
import time

from mcp.server.fastmcp import FastMCP

from app.ai.agent import get_mentor_response
from app.ai.context import build_user_profile
from app.ai.schemas import ChatRequest
from app.database import SessionLocal
from app.config import settings

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
    if settings.MCP_USER_ID is None:
        raise ValueError("MCP_USER_ID is not set in backend/.env")
    request = ChatRequest(message=message)
    with SessionLocal() as db:
        profile = build_user_profile(db, settings.MCP_USER_ID)
    return get_mentor_response(request, profile).response


@mcp.tool()
@logged
def ping() -> str:
    """Check that the Mentora AI MCP server is alive."""
    return "Mentora AI MCP server is running"


class RequireMcpToken:
    """Lets a request reach /mcp only with "Authorization: Bearer <MCP_TOKEN>" (from backend/.env).
    MCP clients can't use the browser's login cookie, so they use this token instead."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if scope["type"] == "http" and (path == "/mcp" or path.startswith("/mcp/")) and not self._allowed(scope):
            body = json.dumps({"detail": "Send Authorization: Bearer <MCP_TOKEN> (set in backend/.env)."}).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [(b"content-type", b"application/json"), (b"www-authenticate", b"Bearer")],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        await self.app(scope, receive, send)

    @staticmethod
    def _allowed(scope) -> bool:
        expected = settings.MCP_TOKEN.get_secret_value().strip() if settings.MCP_TOKEN else ""
        if not expected:
            return False  # no token configured: /mcp is closed
        header = dict(scope.get("headers", [])).get(b"authorization", b"").decode()
        return hmac.compare_digest(header, f"Bearer {expected}")


# Build the ASGI app now so mcp.session_manager exists for main.py's lifespan
mcp_app = RequireMcpToken(mcp.streamable_http_app())