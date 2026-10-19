from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import our settings and models so Alembic can see the tables
from app import models  # noqa: F401  (registers all tables on Base.metadata)
from app.config import settings
from app.database import Base

config = context.config  # the settings from alembic.ini

# Use DATABASE_URL from backend/.env instead of a hardcoded URL in alembic.ini
config.set_main_option("sqlalchemy.url", settings.database_url)

# Logging setup from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The tables `alembic revision --autogenerate` compares the database with
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """`alembic upgrade --sql`: print the SQL instead of running it."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run the migrations against the database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
