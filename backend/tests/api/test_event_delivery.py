import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.bootstrap.composition import build_fake_payments, build_nobody_is_following
from app.bootstrap.events import (
    build_event_delivery_worker,
    build_event_runtime,
)
from app.core.config import Settings
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import get_db
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.event_delivery_worker import EventWorker
from app.infrastructure.events.event_store_model import EventStoreORM


@pytest_asyncio.fixture
async def db_engine(tmp_path):
    """**A connection per session**, which production's pool gives and the
    suite's engine does not (#482).

    `tests/conftest.py` hands every session one SQLite connection so that each
    sees the same in-memory database, which holds while one session at a time is
    using it. This module runs the outbox worker *beside* a request — two
    sessions open at once — and on one connection those are not two
    transactions: closing either session rolls the connection back, and with it
    whatever the other has written and not yet committed. A file lets each
    session hold its own connection, so the worker's poll cannot reach into the
    request's unit of work, as it cannot on Postgres.
    """

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'outbox.sqlite'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


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
    polls = _Polls(session_factory)
    worker = _worker_polling_through(polls)
    worker.start()
    try:
        response = await client.post("/api/v1/users", json=valid_signup_payload)
        assert response.status_code == 201

        # A poll that began after the commit cannot have missed the row.
        await polls.a_whole_poll_from_now()
    finally:
        await worker.stop()

    async with session_factory() as session:
        row = (await session.execute(select(EventOutboxORM))).scalar_one()
    assert row.event_type == "users.user_registered"
    assert row.published_at is not None
    assert row.attempts == 0


async def test_a_poll_between_a_requests_writes_leaves_them_alone(
    app, client, db_engine, session_factory, valid_signup_payload
):
    """**#482, made to happen every time instead of under load.** The worker runs
    beside the API's requests on the same engine, so nothing orders its polls
    against a request's unit of work: one can open, read and close a session
    between the moment a sign-up has written its rows and the moment it commits
    them. Here each flush the sign-up asks for waits for a whole poll before the
    request goes on — the projection flushes and then refreshes, so a poll lands
    between the two — which is that interleaving on purpose.

    On one shared connection it failed exactly as the load did — the poll's
    session closed, the connection rolled back, and the projection's refresh
    found no row: ``Could not refresh instance '<UserORM ...>'``. With a
    connection per session it cannot, which is what makes it a fact about the
    test's engine and not about registration: the event, the projection and the
    outbox row are one transaction, and a poll on its own connection neither
    sees them nor undoes them.
    """

    polls = _Polls(session_factory)

    class _EveryFlushWaitsForAPoll(AsyncSession):
        async def flush(self, objects=None):
            await super().flush(objects)
            await polls.a_whole_poll_from_now()

    request_sessions = async_sessionmaker(
        db_engine, expire_on_commit=False, class_=_EveryFlushWaitsForAPoll
    )

    async def _get_db() -> AsyncIterator[AsyncSession]:
        async with request_sessions() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _get_db

    worker = _worker_polling_through(polls)
    worker.start()
    try:
        response = await client.post("/api/v1/users", json=valid_signup_payload)
        assert response.status_code == 201
        await polls.a_whole_poll_from_now()
    finally:
        await worker.stop()

    async with session_factory() as session:
        row = (await session.execute(select(EventOutboxORM))).scalar_one()
    assert row.published_at is not None


class _Polls:
    """The worker's sessions, counted, so a test waits on a poll and not a timer.

    The worker polls one session at a time, so the n-th session opened is the
    n-th closed, and *a poll that began after now has ended* is a count.
    """

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions
        self._began = 0
        self._ended = 0
        self._changed = asyncio.Condition()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        self._began += 1
        try:
            async with self._sessions() as session:
                yield session
        finally:
            async with self._changed:
                self._ended += 1
                self._changed.notify_all()

    async def a_whole_poll_from_now(self) -> None:
        next_to_begin = self._began + 1
        async with self._changed:
            await asyncio.wait_for(
                self._changed.wait_for(lambda: self._ended >= next_to_begin),
                timeout=5,
            )


def _worker_polling_through(polls: _Polls) -> EventWorker:
    return build_event_delivery_worker(
        event_runtime=build_event_runtime(),
        session_factory=cast(async_sessionmaker[AsyncSession], polls.session),
        settings=Settings(
            WRITER_DB_URL="sqlite+aiosqlite:///:memory:",
            EVENT_DELIVERY_POLL_INTERVAL_SECONDS=0.01,
        ),
        # Nobody is following a sign-up: this test's outbox row reaches a logging
        # handler, and the room teller is the only subscriber a nudge is for.
        nudges=build_nobody_is_following(),
        payments=build_fake_payments(),
    )
