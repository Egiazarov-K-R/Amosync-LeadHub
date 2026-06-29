"""Database connection and session management module.

This module initializes the asynchronous SQLAlchemy engine and session maker
using the application settings. It provides helper utilities and context
managers to safely acquire and release database sessions, preventing connection leaks.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings

# Initialize the asynchronous database engine.
# pool_pre_ping=True automatically checks if the connection is alive before executing queries.
async_engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,  # Set to True if you want to see raw SQL queries in the logs.
)

# Create a session factory configured for asynchronous operations.
# expire_on_commit=False prevents SQLAlchemy from fetching objects again after commit.
async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional asynchronous database session.

    This context manager ensures that the session is properly closed after use,
    and automatically rolls back the transaction if an exception occurs.

    Yields:
        AsyncSession: An active asynchronous SQLAlchemy session.

    Raises:
        Exception: Re-raises any exception that occurs during the transaction
            after performing a safe rollback.
    """
    session: AsyncSession = async_session_maker()
    try:
        yield session
    except Exception as error:
        await session.rollback()
        raise error
    finally:
        await session.close()
