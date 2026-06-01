from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.application.events import EventStreamVersionConflict
from app.bootstrap.events import build_event_runtime
from app.infrastructure.events.sqlalchemy_domain_event_store import (
    SqlAlchemyEventStore,
)
from app.modules.users.domain.events import UserRegistered


def _event(user_id: UUID = UUID(int=42)) -> UserRegistered:
    return UserRegistered(
        user_id=user_id,
        email="alice@example.com",
        nickname="alice",
        password_hash="hash",
        authority="USER",
        is_admin=False,
        is_active=True,
        occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_domain_event_store_appends_and_loads_stream(session_factory):
    user_id = UUID(int=42)
    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)

        stored = await store.append(
            aggregate_type="user",
            aggregate_id=user_id,
            expected_version=0,
            events=[_event(user_id)],
        )
        await session.commit()

        loaded = await store.load_stream(
            aggregate_type="user",
            aggregate_id=user_id,
        )

    assert [event.version for event in stored] == [1]
    assert [event.version for event in loaded] == [1]
    assert loaded[0].event == _event(user_id)


@pytest.mark.asyncio
async def test_domain_event_store_rejects_stale_expected_version(session_factory):
    user_id = UUID(int=43)
    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)
        await store.append(
            aggregate_type="user",
            aggregate_id=user_id,
            expected_version=0,
            events=[_event(user_id)],
        )

        with pytest.raises(EventStreamVersionConflict):
            await store.append(
                aggregate_type="user",
                aggregate_id=user_id,
                expected_version=0,
                events=[_event(user_id)],
            )


@pytest.mark.asyncio
async def test_domain_event_store_converts_unique_violation_to_version_conflict(
    session_factory, monkeypatch
):
    user_id = UUID(int=44)
    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)
        await store.append(
            aggregate_type="user",
            aggregate_id=user_id,
            expected_version=0,
            events=[_event(user_id)],
        )
        await session.commit()

        async def stale_current_version(
            *, aggregate_type: str, aggregate_id: UUID
        ) -> int:
            return 0

        monkeypatch.setattr(store, "_current_version", stale_current_version)

        with pytest.raises(EventStreamVersionConflict):
            await store.append(
                aggregate_type="user",
                aggregate_id=user_id,
                expected_version=0,
                events=[_event(user_id)],
            )
