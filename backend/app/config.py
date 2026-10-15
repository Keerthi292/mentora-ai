"""App settings, loaded from environment variables / backend/.env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Reads DATABASE_URL from the environment or from backend/.env
    database_url: str = "postgresql+psycopg2://mentora:mentora_dev@localhost:5432/mentora"

    # No authentication yet: every request acts as this one demo user.
    # Override with DEMO_USER_ID=... in backend/.env
    DEMO_USER_ID: int = 1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Import this single instance everywhere: `from app.config import settings`
settings = Settings()
