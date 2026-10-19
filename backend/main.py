"""Start the backend for development:  uv run main.py  (from backend/)

Runs on API_HOST:API_PORT from backend/.env and restarts when a file in app/ changes.
"""

from pathlib import Path

import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        reload_dirs=[str(Path(__file__).parent / "app")],
    )
