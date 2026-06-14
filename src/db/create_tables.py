"""
One-time script to create all database tables from models.

Run this script once before starting the main application
to initialize the database schema.
"""

import asyncio

from src.db.base import Base, engine
from src.db import models  # noqa: F401 (import needed to register models)


async def create_tables() -> None:
    """Create all tables defined in models.py if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(create_tables())