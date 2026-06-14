"""
Database models module.

Defines ORM models (tables) for the AmoSync-LeadHub project:
- AmoCRMToken: stores AmoCRM OAuth tokens (single row, overwritten)
- Manager: dealer's managers for round-robin lead distribution
- LeadLog: history of successfully processed leads
"""

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, BigInteger, DateTime, Boolean

from src.db.base import Base


class AmoCRMToken(Base):
    """Stores AmoCRM OAuth tokens. Always contains a single row that gets overwritten."""

    __tablename__ = "amocrm_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    access_token: Mapped[str] = mapped_column(String(255))
    refresh_token: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class Manager(Base):
    """Dealer's managers list used for round-robin lead distribution."""

    __tablename__ = "managers"

    id: Mapped[int] = mapped_column(primary_key=True)
    amo_user_id: Mapped[int] = mapped_column(BigInteger)
    tg_username: Mapped[str] = mapped_column(String(100))
    tg_chat_id: Mapped[int] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_assigned_at: Mapped[datetime] = mapped_column(DateTime)


class LeadLog(Base):
    """History of successfully processed leads, used for deduplication."""

    __tablename__ = "lead_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_lead_id: Mapped[str] = mapped_column(String(100), unique=True)
    client_name: Mapped[str] = mapped_column(String(100))
    client_phone: Mapped[str] = mapped_column(String(20))
    amo_lead_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime)