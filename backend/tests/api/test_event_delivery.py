import asyncio

import pytest
from sqlalchemy import select

from app.bootstrap.composition import build_scoring_contexts
from app.bootstrap.events import (
    build_event_delivery_worker,
    build_event_runtime,
)
from app.core.config import Settings
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.event_store_model import EventStoreORM


@pytest.mark.asyncio
async def test_signup_writes_stable_event_delivery_contract(
    client, session_factory, valid_signup_payload
):
    response = await client.post("/api/v1/users", json=valid_signup_payload)
    assert response.status_code == 201

    async with session_factory() as session:
        delivery_rows = (
            await session.execute(select(EventOutboxORM))
        ).scalars().all()
        stored_events = (await session.execute(select(EventStoreORM))).scalars().all()

    assert len(stored_events) == 1
    assert stored_events[0].aggregate_type == "user"
    assert stored_events[0].version == 1
    assert stored_events[0].event_type == "users.user_registered"
    assert stored_events[0].payload["password_hash"]
    assert len(delivery_rows) == 1
    assert delivery_rows[0].event_type == "users.user_registered"
    assert delivery_rows[0].schema_version == 1
    assert delivery_rows[0].published_at is None


@pytest.mark.asyncio
async def test_signup_event_is_delivered_by_embedded_worker(
    client, session_factory, valid_signup_payload
):
    """The embedded worker publishes what a request enqueued.

    **The request is served before the worker starts, and that ordering is the
    test rather than an accident of writing.** The suite's engine is in-memory
    SQLite on a `StaticPool`, which is one DBAPI connection handed to every
    session — so a poll that opens a read transaction and closes it rolls back
    whatever the request had in flight on the same connection. That is a
    property of the harness and not of the worker: in a served process each
    session takes its own connection from the pool, and a poller's rollback
    reaches nothing but its own.

    Running them concurrently was therefore never testing concurrency, only
    losing a race often enough to matter — and it went unnoticed while the tick
    ran one short query. It runs two now (ADR-0076's match wakes), and the
    window is wide enough to lose most of the time. What this test claims is
    that the worker delivers, and it claims it here without the race.
    """

    response = await client.post("/api/v1/users", json=valid_signup_payload)
    assert response.status_code == 201

    settings = Settings(
        WRITER_DB_URL="sqlite+aiosqlite:///:memory:",
        EVENT_DELIVERY_POLL_INTERVAL_SECONDS=0.01,
    )
    worker = build_event_delivery_worker(
        event_runtime=build_event_runtime(),
        session_factory=session_factory,
        settings=settings,
        scoring_contexts=build_scoring_contexts(),
    )
    worker.start()
    try:
        row = None
        for _ in range(100):
            async with session_factory() as session:
                row = (await session.execute(select(EventOutboxORM))).scalar_one()
            if row.published_at is not None:
                break
            await asyncio.sleep(0.01)

        assert row is not None
        assert row.event_type == "users.user_registered"
        assert row.published_at is not None
        assert row.attempts == 0
    finally:
        await worker.stop()
