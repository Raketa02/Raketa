"""Putting one real event in the log — for a test that needs a fact no route
takes dictation for: a chosen Level, a profile filed at a chosen instant."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.events import build_event_runtime
from app.infrastructure.events.event_store_model import EventStoreORM
from app.shared.domain import DomainEvent


async def append(
    session_factory: async_sessionmaker[AsyncSession],
    event: DomainEvent,
    *,
    aggregate_type: str = "PlayerProfile",
    aggregate_id: UUID | None = None,
    sequence_no: int | None = None,
    version: int = 1,
) -> int:
    """Put one event in the log and answer the position it took.

    ``sequence_no`` is settable so a test can leave a **hole**, which is the one
    thing the log's own identity column will never do on request. ``version`` is
    settable so a second event can land on the **same** stream — the store keys
    ``(aggregate, version)`` unique, so two events filed under one id at
    version 1 are a constraint violation and not a stream.
    """

    runtime = build_event_runtime()
    encoded = runtime.codec.encode(event)
    async with session_factory() as session:
        async with session.begin():
            row = EventStoreORM(
                id=uuid4(),
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id or uuid4(),
                version=version,
                event_type=encoded.event_type,
                schema_version=encoded.schema_version,
                payload=encoded.payload,
                occurred_at=event.occurred_at,
                created_at=event.occurred_at,
            )
            if sequence_no is not None:
                row.sequence_no = sequence_no
            session.add(row)
        return row.sequence_no
