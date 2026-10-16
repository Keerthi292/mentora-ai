from mcp.server.fastmcp import FastMCP

from app.ai.agent import get_mentor_response
from app.ai.context import build_user_profile
from app.ai.schemas import ChatRequest
from app.database import SessionLocal
from app.dependencies import get_current_user_id

# stateless_http + json_response keeps Streamable HTTP simple for a first version
mcp = FastMCP("Mentora AI", stateless_http=True, json_response=True)


@mcp.tool()
def ask_mentor(message: str) -> str:
    """Ask the Mentora AI mentor a learning or career question."""
    request = ChatRequest(message=message)
    with SessionLocal() as db:
        profile = build_user_profile(db, get_current_user_id())
    return get_mentor_response(request, profile).response


@mcp.tool()
def ping() -> str:
    """Check that the Mentora AI MCP server is alive."""
    return "Mentora AI MCP server is running"


# Build the ASGI app now so mcp.session_manager exists for main.py's lifespan
mcp_app = mcp.streamable_http_app()