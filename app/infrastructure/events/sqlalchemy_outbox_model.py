from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class EventOutboxORM(Base):
    """Transactional outbox row. Written in the same SQL transaction as the
    aggregate that produced the event; published asynchronously by the
    OutboxRelay.

    `payload` uses JSONB on PostgreSQL (indexable, binary storage) and falls
    back to plain JSON elsewhere so the same code drives SQLite-based tests.
    """

    __tablename__ = "event_outbox"
    __table_args__ = (
        Index(
            "ix_event_outbox_pending",
            "published_at",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
