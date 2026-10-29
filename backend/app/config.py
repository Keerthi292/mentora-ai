"""App settings, loaded from environment variables / backend/.env."""

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Private addresses and passwords live only in backend/.env (see .env.example), never in code.
    # DATABASE_URL, e.g. postgresql+psycopg2://USER:PASSWORD@HOST:5432/DATABASE
    database_url: str
    # Where `python main.py` runs the backend locally (the frontend's dev server reads them too).
    # A host like Render starts uvicorn with its own --host/--port instead.
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8002
    # Other sites allowed to call the API from a browser, comma-separated. Usually not needed:
    # the frontend calls /api on its own address and that is forwarded to the backend.
    CORS_ORIGINS: str = ""

    # Logins: a session lasts this many days. COOKIE_SECURE=true when served over HTTPS.
    SESSION_DAYS: int = Field(30, ge=1)
    COOKIE_SECURE: bool = False

    # "Forgot password" emails. APP_URL is where the frontend runs (the reset link points there).
    # Without SMTP_HOST no email is sent: the reset link is printed in the backend's terminal
    # instead (fine on your own computer). Reset links work for RESET_TOKEN_MINUTES.
    APP_URL: str = "http://localhost:5173"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: SecretStr | None = None
    SMTP_FROM: str = ""
    RESET_TOKEN_MINUTES: int = Field(30, ge=5)

    # MCP (/mcp) can't use a browser login: clients send "Authorization: Bearer <MCP_TOKEN>"
    # and the tools act as MCP_USER_ID. Without MCP_TOKEN, /mcp refuses every request.
    MCP_TOKEN: SecretStr | None = None
    MCP_USER_ID: int | None = None

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

    @field_validator("database_url")
    @classmethod
    def use_psycopg2(cls, url: str) -> str:
        """Hosts like Render give postgres:// or postgresql:// URLs without a driver; SQLAlchemy
        would then pick psycopg (v3), but the app installs psycopg2."""
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg2://" + url.removeprefix(prefix)
        return url

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Absolute path, so backend/.env is found whatever folder the app starts from
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", extra="ignore"
    )


# Import this single instance everywhere: `from app.config import settings`
settings = Settings()
