"""Alembic migration environment configuration module.

This module acts as the orchestration environment for running database schema
migrations. It configures the database engine dynamically using application
settings and associates SQLAlchemy declarative metadata to enable automated
migration generation ('autogenerate').

Usage:
    To generate a new migration automatically based on model changes:
        $ alembic revision --autogenerate -m "Description of changes"

    To apply all pending migrations to the database:
        $ alembic upgrade head

    To rollback the last applied migration:
        $ alembic downgrade -1
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import application settings and declarative base
from src.db.base import Base
from core.config import settings

# Explicitly import all models to ensure they are registered on the Base metadata.
# Without these imports, Alembic will fail to detect existing models and schemas
# during autogeneration, leading to destructive drop-table generation.
from src.db.models import AmoCRMToken, LeadLog, Manager, LeadStatus  # noqa: F401

# Retrieve Alembic configuration object
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically as configured in alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Dynamically inject the database URL from settings to keep credentials secure
# Escape '%' characters to '%%' to prevent Alembic's ConfigParser from interpreting them
# as string interpolation variables (e.g., in URL-encoded passwords with %26, %23, etc.)
escaped_db_url = settings.database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", escaped_db_url)

# Set up metadata object for autogenerate support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well. By skipping the Engine creation
    we can even run migrations without having a live database connection,
    allowing the generation of raw SQL scripts.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Execute migration scripts within an established database connection.

    Args:
        connection: The active SQLAlchemy Connection object.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context. Since our database stack is completely asynchronous (asyncpg),
    we utilize an asynchronous engine configuration.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

# select a mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())