import asyncio

import pytest
from sqlalchemy import select

from app.bootstrap.composition import build_nobody_is_following
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
    settings = Settings(
        WRITER_DB_URL="sqlite+aiosqlite:///:memory:",
        EVENT_DELIVERY_POLL_INTERVAL_SECONDS=0.01,
    )
    worker = build_event_delivery_worker(
        event_runtime=build_event_runtime(),
        session_factory=session_factory,
        settings=settings,
        # Nobody is following a sign-up: this test's outbox row reaches a logging
        # handler, and the room teller is the only subscriber a nudge is for.
        nudges=build_nobody_is_following(),
    )
    worker.start()
    try:
        response = await client.post("/api/v1/users", json=valid_signup_payload)
        assert response.status_code == 201

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
