from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.events import SerializedEventEnvelope
from app.infrastructure.database import models as _models  # noqa: F401
from app.infrastructure.database.base import Base
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


@pytest.mark.asyncio
async def test_postgresql_concurrent_fetchers_do_not_receive_locked_event():
    url = os.environ.get("EVENT_TEST_DATABASE_URL", "")
    if not url.startswith(("postgresql://", "postgresql+asyncpg://", "postgres://")):
        pytest.skip("Set EVENT_TEST_DATABASE_URL to exercise PostgreSQL claim safety")
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]
    elif url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]

    engine = create_async_engine(url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    record = _record(record_id=uuid4())
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            await SqlAlchemyOutboxRepository(session).add_many([record])
            await session.commit()

        first_fetched = asyncio.Event()
        release_first = asyncio.Event()

        async def fetch_and_hold():
            async with session_factory() as session:
                rows = await SqlAlchemyOutboxRepository(session).fetch_pending(
                    batch_size=1
                )
                first_fetched.set()
                await release_first.wait()
                return rows

        async def fetch():
            async with session_factory() as session:
                return await SqlAlchemyOutboxRepository(session).fetch_pending(
                    batch_size=1
                )

        first_task = asyncio.create_task(fetch_and_hold())
        await asyncio.wait_for(first_fetched.wait(), timeout=5)
        second = await fetch()
        release_first.set()
        first = await first_task

        assert [row.id for row in first] == [record.id]
        assert second == []
    finally:
        async with session_factory() as session:
            await session.execute(
                delete(EventOutboxORM).where(EventOutboxORM.id == record.id)
            )
            await session.commit()
        await engine.dispose()
