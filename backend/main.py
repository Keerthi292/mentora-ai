"""Start the backend for development:  uv run main.py  (from backend/)

Runs on http://127.0.0.1:8002 and restarts when a file in app/ changes.
"""

from pathlib import Path

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8002,
        reload=True,
        reload_dirs=[str(Path(__file__).parent / "app")],
    )
