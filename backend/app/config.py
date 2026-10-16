"""App settings, loaded from environment variables / backend/.env."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Reads DATABASE_URL from the environment or from backend/.env
    database_url: str = "postgresql+psycopg2://mentora:mentora_dev@localhost:5432/mentora"

    # No authentication yet: every request acts as this one demo user.
    # Override with DEMO_USER_ID=... in backend/.env
    DEMO_USER_ID: int = 1

    # Gemini (Google Gen AI SDK). Get a key at https://aistudio.google.com/apikey
    # and put GEMINI_API_KEY=... in backend/.env. SecretStr keeps the key out of
    # logs and reprs; read it with settings.GEMINI_API_KEY.get_secret_value().
    GEMINI_API_KEY: SecretStr | None = None
    # Change models without touching code, e.g. GEMINI_MODEL=gemini-3.8-flash
    GEMINI_MODEL: str = "gemini-3.5-flash"
    # Give up on a Gemini request after this many seconds
    GEMINI_TIMEOUT_SECONDS: float = 60
    # How many earlier chat messages (user + mentor) are sent with each new one.
    # Older messages are left out to keep requests fast and cheap; 0 = no history.
    CHAT_HISTORY_LIMIT: int = Field(20, ge=0)

    # Uploaded files (chat attachments, project images) are saved here. Not in Git.
    UPLOAD_DIR: Path = BACKEND_DIR / "uploads"
    MAX_UPLOAD_MB: int = Field(20, ge=1)

    # Absolute path, so backend/.env is found whatever folder the app starts from
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", extra="ignore"
    )


# Import this single instance everywhere: `from app.config import settings`
settings = Settings()
