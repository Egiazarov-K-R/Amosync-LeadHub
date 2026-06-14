from core.config import settings
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(settings.database_url, echo=True) # connect to PostgreSQL database
async_session = async_sessionmaker(engine, expire_on_commit=False) # method of exchanging queries with a database

class Base(DeclarativeBase): # database description class
    pass