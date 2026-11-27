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


def _event(
    user_id: UUID = UUID(int=42),
    occurred_at: datetime = datetime(2026, 1, 1, tzinfo=timezone.utc),
) -> UserRegistered:
    return UserRegistered(
        user_id=user_id,
        email="alice@example.com",
        password_hash="hash",
        authority="USER",
        is_admin=False,
        is_active=True,
        occurred_at=occurred_at,
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


@pytest.mark.asyncio
async def test_append_order_is_total_across_streams(session_factory):
    # `version` orders one stream. Nothing ordered two until `sequence_no`: the
    # primary key was a random UUID, and both indexes were per-stream.
    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)

        first = await store.append(
            aggregate_type="user",
            aggregate_id=UUID(int=51),
            expected_version=0,
            events=[_event(UUID(int=51))],
        )
        second = await store.append(
            aggregate_type="user",
            aggregate_id=UUID(int=52),
            expected_version=0,
            events=[_event(UUID(int=52))],
        )
        await session.commit()

    assert first[0].sequence_no < second[0].sequence_no


@pytest.mark.asyncio
async def test_events_appended_in_one_call_get_distinct_positions(session_factory):
    # The case `occurred_at` cannot express at all: a commit that appends several
    # events sharing one instant, which is how the profile-creating commit writes
    # (ADR-0089). Same moment, still a defined order.
    user_id = UUID(int=53)
    instant = datetime(2026, 2, 2, tzinfo=timezone.utc)
    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)

        stored = await store.append(
            aggregate_type="user",
            aggregate_id=user_id,
            expected_version=0,
            events=[_event(user_id, instant), _event(user_id, instant)],
        )
        await session.commit()

    assert {event.occurred_at for event in stored} == {instant}
    positions = [event.sequence_no for event in stored]
    assert positions == sorted(set(positions))


@pytest.mark.asyncio
async def test_which_addressed_streams_hold_an_event_is_answered_about_them_alone(
    session_factory,
):
    """**Addressed, never searched**: the streams named, each answered once
    however many events it holds, a stream of another aggregate type under the
    same id never counted, and a stream nobody asked about never answered."""

    held = UUID(int=71)
    twice = UUID(int=72)
    other_type = UUID(int=73)
    not_asked = UUID(int=74)
    never_written = UUID(int=75)
    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)
        for aggregate_type, aggregate_id, events in (
            ("user", held, [_event(held)]),
            ("user", twice, [_event(twice), _event(twice)]),
            ("someone_else", other_type, [_event(other_type)]),
            ("user", not_asked, [_event(not_asked)]),
        ):
            await store.append(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                expected_version=0,
                events=events,
            )
        await session.commit()

        present = await store.streams_present(
            aggregate_type="user",
            aggregate_ids=[held, twice, other_type, never_written],
        )

    assert present == frozenset({held, twice})


async def test_a_batch_loads_each_addressed_stream_whole_and_in_order_in_one_statement(
    session_factory, statements
):
    """``load_stream`` for a batch (#814): each stream named, its events oldest
    first — exactly what a load of it returns — one of another aggregate type
    under the same id never loaded, one nobody asked about never answered, and
    one never written absent. **One statement**, however many are asked."""

    held = UUID(int=81)
    twice = UUID(int=82)
    other_type = UUID(int=83)
    not_asked = UUID(int=84)
    never_written = UUID(int=85)
    first = datetime(2026, 1, 1, tzinfo=timezone.utc)
    second = datetime(2026, 2, 1, tzinfo=timezone.utc)
    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)
        for aggregate_type, aggregate_id, events in (
            ("user", twice, [_event(twice, first), _event(twice, second)]),
            ("user", held, [_event(held)]),
            ("someone_else", other_type, [_event(other_type)]),
            ("user", not_asked, [_event(not_asked)]),
        ):
            await store.append(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                expected_version=0,
                events=events,
            )
        await session.commit()

        with statements.counting() as sent:
            loaded = await store.load_streams(
                aggregate_type="user",
                aggregate_ids=[held, twice, other_type, never_written, held],
            )
        one_by_one = {
            aggregate_id: await store.load_stream(
                aggregate_type="user", aggregate_id=aggregate_id
            )
            for aggregate_id in (held, twice)
        }

    assert len(sent) == 1
    assert set(loaded) == {held, twice}
    assert [event.version for event in loaded[twice]] == [1, 2]
    assert [event.event.occurred_at for event in loaded[twice]] == [first, second]
    assert loaded == one_by_one


async def test_a_batch_of_no_streams_loads_nothing_and_asks_nothing(
    session_factory, monkeypatch
):
    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)

        async def no_statement(*args, **kwargs):
            raise AssertionError("an empty batch is not sent to the database")

        monkeypatch.setattr(session, "execute", no_statement)

        loaded = await store.load_streams(aggregate_type="user", aggregate_ids=[])

    assert loaded == {}


@pytest.mark.asyncio
async def test_a_stream_appended_in_this_transaction_is_present_before_commit(
    session_factory,
):
    """The same session as the write: an append a moment ago is visible to the
    question that follows it, as ``load_stream`` would show it."""

    user_id = UUID(int=76)
    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)
        await store.append(
            aggregate_type="user",
            aggregate_id=user_id,
            expected_version=0,
            events=[_event(user_id)],
        )

        present = await store.streams_present(
            aggregate_type="user", aggregate_ids=[user_id]
        )

    assert present == frozenset({user_id})


@pytest.mark.asyncio
async def test_asking_which_of_no_streams_exist_answers_nothing_and_asks_nothing(
    session_factory, monkeypatch
):
    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)

        async def no_statement(*args, **kwargs):
            raise AssertionError("an empty question is not sent to the database")

        monkeypatch.setattr(session, "execute", no_statement)

        present = await store.streams_present(aggregate_type="user", aggregate_ids=[])

    assert present == frozenset()


@pytest.mark.asyncio
async def test_cross_stream_finder_reads_append_order_not_domain_time(session_factory):
    """The finder is ordered by when the row was written, not what it claims.

    Its callers tie-break on this: ``_newest_open_by_sport`` scans the list in
    reverse to pick the run to resume. So the two streams here are opened with
    ``occurred_at`` *inverted* against their append order — a store ordered by
    domain time hands back the wrong one, and the old query did exactly that.
    """

    older_moment = datetime(2026, 1, 1, tzinfo=timezone.utc)
    newer_moment = datetime(2026, 6, 1, tzinfo=timezone.utc)
    appended_first = UUID(int=61)
    appended_second = UUID(int=62)

    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, build_event_runtime().codec)

        await store.append(
            aggregate_type="user",
            aggregate_id=appended_first,
            expected_version=0,
            # Appended first, but claims the *later* moment.
            events=[_event(appended_first, newer_moment)],
        )
        await store.append(
            aggregate_type="user",
            aggregate_id=appended_second,
            expected_version=0,
            events=[_event(appended_second, older_moment)],
        )
        await session.commit()

        found = await store.find_aggregate_ids_by_first_event(
            aggregate_type="user",
            payload_equals={"email": "alice@example.com"},
        )

    assert found == [appended_first, appended_second]
