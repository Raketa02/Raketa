from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Identity,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base

# BIGSERIAL on PostgreSQL; on SQLite an INTEGER PRIMARY KEY, which is that
# dialect's rowid alias and the only column it will auto-assign. The variant is
# what makes the *same* ordering guarantee hold under the in-memory SQLite the
# suite runs on and the Postgres the application runs on. Widening SQLite to
# BIGINT would break it silently: SQLite only auto-assigns a column spelled
# exactly `INTEGER PRIMARY KEY`, so the rows would arrive with no sequence at all.
APPEND_SEQUENCE = BigInteger().with_variant(Integer(), "sqlite")


class EventStoreORM(Base):
    """Append-only domain event stream used as the write-side source of truth.

    Two orders live in this table and they are not the same order.

    `version` orders one stream and nothing else. It is the aggregate's own
    count, so it says nothing about how two streams interleave.

    `sequence_no` is the **append order of the whole store** — the position a row
    took in the log, assigned by the database at insert. It is the only total
    order here, and the only column a read *across* streams may order by. It is
    the primary key because that is what an append-only log is keyed by; the
    event's `id` stays a UUID and stays unique, but a random identifier carries
    no order and never did.

    `occurred_at` is the **domain moment**, and is deliberately not a total
    order even in principle: one commit may append several events sharing an
    instant, on the same stream or on different ones. `created_at` is no better
    — `func.now()` is transaction start time in Postgres, identical for every row
    written in one transaction.
    """

    __tablename__ = "event_store"
    __table_args__ = (
        UniqueConstraint(
            "aggregate_type",
            "aggregate_id",
            "version",
            name="uq_event_store_stream_version",
        ),
        UniqueConstraint("id", name="uq_event_store_id"),
        Index(
            "ix_event_store_stream",
            "aggregate_type",
            "aggregate_id",
            "version",
        ),
    )

    sequence_no: Mapped[int] = mapped_column(
        APPEND_SEQUENCE, Identity(always=False), primary_key=True
    )
    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    schema_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    payload: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
