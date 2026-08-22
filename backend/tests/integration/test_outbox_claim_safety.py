"""Two outbox workers never claim the same event — asserted against Postgres.

`SELECT ... FOR UPDATE SKIP LOCKED` is what makes a second delivery worker safe
to run, and it is Postgres-only: SQLite has no row locks to skip, so on the API
suite's in-memory database this reads as two workers both fetching the same
event and both publishing it.

**This case is a move, not a new test.** It lived in
`tests/unit/test_sqlalchemy_event_store.py` and skipped unless
`EVENT_TEST_DATABASE_URL` was set — a variable set by the same workflow file
that would be edited to remove it, so the pipeline could stop running it without
turning anything red. That is the shape #62 exists to remove, and it was the one
existing instance of it in the tree. On the harness in this directory the
requirement is keyed on `CI`, which the workflow does not own.

The behaviour asserted is unchanged; only where it lives and whether it can go
quiet have changed.
"""

import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.application.events import SerializedEventEnvelope
from app.infrastructure.database import models as _models  # noqa: F401
from app.infrastructure.database.base import Base
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.sqlalchemy_event_delivery_queue import (
    SqlAlchemyOutboxRepository,
)

pytestmark = pytest.mark.postgres


def _record(record_id: UUID) -> SerializedEventEnvelope:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return SerializedEventEnvelope(
        id=record_id,
        event_type="tests.sample",
        schema_version=1,
        payload={"occurred_at": now.isoformat()},
        occurred_at=now,
    )


@pytest.mark.asyncio
async def test_concurrent_fetchers_do_not_receive_a_locked_event(pg_engine):
    session_factory = async_sessionmaker(pg_engine, expire_on_commit=False)
    record = _record(uuid4())
    try:
        async with pg_engine.begin() as connection:
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
