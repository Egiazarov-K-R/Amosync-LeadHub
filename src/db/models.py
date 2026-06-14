"""
Database models for AmoSync-LeadHub.

Defines the SQLAlchemy ORM models representing the database schema:
tokens, managers, and lead logs.
"""

from enum import Enum
from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, BigInteger, DateTime, Boolean, ForeignKey, Integer

from src.db.base import Base


class LeadStatus(str, Enum):
    """
    Enum representing all possible states of a captured lead.
    """
    NEW = "new"                  # Just captured, waiting for processing
    CRM_OFFLINE = "crm_offline"  # AmoCRM was down, lead sent directly to TG
    DISTRIBUTED = "distributed"  # Manager assigned, notified in TG, pending sync
    SYNCED = "synced"            # Successfully created in both TG and AmoCRM
    DUPLICATE = "duplicate"      # Duplicate lead, ignored from processing


class AmoCRMToken(Base):
    """
    Stores AmoCRM OAuth tokens. Always keeps exactly 1 row in the table.
    """
    __tablename__ = "amocrm_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    access_token: Mapped[str] = mapped_column(String(1000))  # Access token can be very long
    refresh_token: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Manager(Base):
    """
    Dealer's managers list used for Round-Robin lead distribution.
    """
    __tablename__ = "managers"

    id: Mapped[int] = mapped_column(primary_key=True)
    amo_user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    tg_username: Mapped[str] = mapped_column(String(100))
    tg_chat_id: Mapped[int] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_assigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationship to link with LeadLogs
    leads = relationship("LeadLog", back_populates="manager")


class LeadLog(Base):
    """
    History of successfully processed leads, used for deduplication and audit.
    """
    __tablename__ = "lead_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_lead_id: Mapped[str] = mapped_column(String(100), unique=True)
    client_name: Mapped[str] = mapped_column(String(100))
    client_phone: Mapped[str] = mapped_column(String(20))
    price: Mapped[int] = mapped_column(Integer)
    
    # Store Enum as a String in the database
    status: Mapped[LeadStatus] = mapped_column(String(50), default=LeadStatus.NEW)
    
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("managers.id"), nullable=True)
    amo_lead_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to get manager info easily
    manager = relationship("Manager", back_populates="leads")
