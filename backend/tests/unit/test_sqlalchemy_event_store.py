from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy import select

from app.application.events import SerializedEventEnvelope
from app.infrastructure.database import models as _models  # noqa: F401
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.sqlalchemy_event_delivery_queue import (
    SqlAlchemyOutboxRepository,
)


def _record(record_id: int | UUID = 1) -> SerializedEventEnvelope:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return SerializedEventEnvelope(
        id=record_id if isinstance(record_id, UUID) else UUID(int=record_id),
        event_type="tests.sample",
        schema_version=1,
        payload={"occurred_at": now.isoformat()},
        occurred_at=now,
    )


@pytest.mark.asyncio
async def test_sqlalchemy_event_delivery_queue_fetches_and_publishes_pending(
    session_factory,
):
    now = datetime(2026, 1, 2, tzinfo=timezone.utc)
    async with session_factory() as session:
        store = SqlAlchemyOutboxRepository(session)
        await store.add_many([_record()])
        await session.commit()
        pending = await store.fetch_pending(
            batch_size=1,
        )

        assert pending[0].attempts == 0
        assert pending[0].published_at is None
        await store.mark_published(pending[0].id, at=now)

        row = (
            await session.execute(
                select(EventOutboxORM).where(EventOutboxORM.id == pending[0].id)
            )
        ).scalar_one()
        assert row.published_at is not None
        assert row.published_at.replace(tzinfo=timezone.utc) == now
        assert row.last_error is None
        assert await store.fetch_pending(batch_size=1) == []


@pytest.mark.asyncio
async def test_sqlalchemy_event_delivery_queue_marks_failed_without_publishing(
    session_factory,
):
    async with session_factory() as session:
        store = SqlAlchemyOutboxRepository(session)
        await store.add_many([_record()])
        await session.commit()
        pending = (await store.fetch_pending(batch_size=1))[0]
        await store.mark_failed(pending.id, error="retry", attempts=1)

        row = (
            await session.execute(
                select(EventOutboxORM).where(EventOutboxORM.id == pending.id)
            )
        ).scalar_one()
        assert row.published_at is None
        assert row.attempts == 1
        assert row.last_error == "retry"
        assert (await store.fetch_pending(batch_size=1))[0].id == pending.id
