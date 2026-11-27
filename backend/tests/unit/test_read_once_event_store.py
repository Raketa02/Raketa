"""A deck read loads each event stream once (#704, ADR-0197 §2c).

``ReadOnceEventStore`` sits over the store for the life of one read-only
request: the first load of a stream is a load, every later one is the same
list, and two in flight together are one load. It is wired into the deck read's
composition alone — never into a use case that writes — but if a write ever
did reach it, an append forgets the stream it appended to, so a reload still
sees its own events.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Collection, Iterable, Mapping
from uuid import UUID, uuid4

import pytest

from app.application.events.store import StoredDomainEvent
from app.infrastructure.events.read_once_event_store import ReadOnceEventStore
from app.shared.domain import DomainEvent

PROFILE = "player_profile"
RATING = "rating"
ALICE = UUID("11111111-1111-1111-1111-111111111111")
BOB = UUID("22222222-2222-2222-2222-222222222222")


@dataclass(frozen=True)
class Happened:
    occurred_at: datetime = field(
        default_factory=lambda: datetime(2026, 10, 5, 8, tzinfo=timezone.utc)
    )


def stored(aggregate_type: str, aggregate_id: UUID, version: int) -> StoredDomainEvent:
    return StoredDomainEvent(
        id=uuid4(),
        sequence_no=version,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        version=version,
        event=Happened(),
        occurred_at=datetime(2026, 10, 5, 8, tzinfo=timezone.utc),
        created_at=datetime(2026, 10, 5, 8, tzinfo=timezone.utc),
    )


class CountingStore:
    """A ``DomainEventStore`` that counts its loads and can be held mid-load."""

    def __init__(self) -> None:
        self.streams: dict[tuple[str, UUID], list[StoredDomainEvent]] = {}
        self.loads: list[tuple[str, UUID]] = []
        self.searches: list[tuple[str, tuple[tuple[str, str], ...]]] = []
        self.presences: list[tuple[str, frozenset[UUID]]] = []
        self.batches: list[tuple[str, tuple[UUID, ...]]] = []
        self.hold: asyncio.Event | None = None
        self.fail_next = False

    async def append(
        self,
        *,
        aggregate_type: str,
        aggregate_id: UUID,
        expected_version: int,
        events: Iterable[DomainEvent],
    ) -> list[StoredDomainEvent]:
        stream = self.streams.setdefault((aggregate_type, aggregate_id), [])
        rows = [
            stored(aggregate_type, aggregate_id, expected_version + offset)
            for offset, _ in enumerate(events, start=1)
        ]
        stream.extend(rows)
        return rows

    async def load_stream(
        self, *, aggregate_type: str, aggregate_id: UUID
    ) -> list[StoredDomainEvent]:
        self.loads.append((aggregate_type, aggregate_id))
        if self.hold is not None:
            await self.hold.wait()
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("the store is down")
        return list(self.streams.get((aggregate_type, aggregate_id), []))

    async def load_streams(
        self, *, aggregate_type: str, aggregate_ids: Collection[UUID]
    ) -> Mapping[UUID, list[StoredDomainEvent]]:
        self.batches.append((aggregate_type, tuple(aggregate_ids)))
        return {
            aggregate_id: list(stream)
            for aggregate_id in aggregate_ids
            if (stream := self.streams.get((aggregate_type, aggregate_id)))
        }

    async def streams_present(
        self, *, aggregate_type: str, aggregate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        self.presences.append((aggregate_type, frozenset(aggregate_ids)))
        return frozenset(
            aggregate_id
            for aggregate_id in aggregate_ids
            if self.streams.get((aggregate_type, aggregate_id))
        )

    async def find_aggregate_ids_by_first_event(
        self, *, aggregate_type: str, payload_equals: Mapping[str, str]
    ) -> list[UUID]:
        self.searches.append((aggregate_type, tuple(sorted(payload_equals.items()))))
        return [
            aggregate_id
            for kind, aggregate_id in self.streams
            if kind == aggregate_type
        ]


@pytest.fixture
def inner() -> CountingStore:
    store = CountingStore()
    store.streams[(PROFILE, ALICE)] = [
        stored(PROFILE, ALICE, 1),
        stored(PROFILE, ALICE, 2),
    ]
    store.streams[(RATING, ALICE)] = [stored(RATING, ALICE, 1)]
    return store


async def test_a_stream_is_loaded_once_and_every_later_read_is_the_same_list(
    inner: CountingStore,
) -> None:
    once = ReadOnceEventStore(inner)

    first = await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)
    second = await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)
    third = await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)

    assert inner.loads == [(PROFILE, ALICE)]
    assert first == second == third == inner.streams[(PROFILE, ALICE)]


async def test_a_different_stream_is_its_own_load(inner: CountingStore) -> None:
    """Keyed on type *and* id: a profile and a rating filed under one player's
    id are two streams, and an absent stream is remembered as absent."""

    once = ReadOnceEventStore(inner)

    await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)
    await once.load_stream(aggregate_type=RATING, aggregate_id=ALICE)
    assert await once.load_stream(aggregate_type=PROFILE, aggregate_id=BOB) == []
    assert await once.load_stream(aggregate_type=PROFILE, aggregate_id=BOB) == []

    assert inner.loads == [(PROFILE, ALICE), (RATING, ALICE), (PROFILE, BOB)]


async def test_a_reader_cannot_change_what_the_next_reader_is_handed(
    inner: CountingStore,
) -> None:
    once = ReadOnceEventStore(inner)

    first = await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)
    first.clear()

    assert len(await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)) == 2


async def test_two_loads_in_flight_together_are_one_load(inner: CountingStore) -> None:
    once = ReadOnceEventStore(inner)
    inner.hold = asyncio.Event()

    both = asyncio.gather(
        once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE),
        once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE),
    )
    await asyncio.sleep(0)
    assert inner.loads == [(PROFILE, ALICE)]
    inner.hold.set()
    first, second = await both

    assert first == second == inner.streams[(PROFILE, ALICE)]
    assert inner.loads == [(PROFILE, ALICE)]


async def test_a_load_that_failed_is_not_remembered_as_an_answer(
    inner: CountingStore,
) -> None:
    once = ReadOnceEventStore(inner)
    inner.fail_next = True

    with pytest.raises(RuntimeError):
        await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)
    recovered = await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)

    assert recovered == inner.streams[(PROFILE, ALICE)]
    assert inner.loads == [(PROFILE, ALICE), (PROFILE, ALICE)]


async def test_a_waiter_on_a_failed_load_sees_the_failure_and_may_retry(
    inner: CountingStore,
) -> None:
    once = ReadOnceEventStore(inner)
    inner.hold = asyncio.Event()
    inner.fail_next = True

    both = asyncio.gather(
        once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE),
        once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE),
        return_exceptions=True,
    )
    await asyncio.sleep(0)
    inner.hold.set()
    outcomes = await both

    assert all(isinstance(outcome, RuntimeError) for outcome in outcomes)
    assert (
        await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)
        == (inner.streams[(PROFILE, ALICE)])
    )


async def test_an_append_forgets_the_stream_so_a_reload_sees_its_own_events(
    inner: CountingStore,
) -> None:
    """Never wired into a write path — but if one reached it, the answer must
    still be the store's, not a stale copy from before the append."""

    once = ReadOnceEventStore(inner)
    before = await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)

    appended = await once.append(
        aggregate_type=PROFILE,
        aggregate_id=ALICE,
        expected_version=len(before),
        events=[Happened()],
    )
    after = await once.load_stream(aggregate_type=PROFILE, aggregate_id=ALICE)

    assert [row.version for row in appended] == [3]
    assert [row.version for row in after] == [1, 2, 3]
    assert (
        await once.load_stream(aggregate_type=RATING, aggregate_id=ALICE)
        == (inner.streams[(RATING, ALICE)])
    )
    assert inner.loads == [(PROFILE, ALICE), (PROFILE, ALICE), (RATING, ALICE)]


async def test_a_search_by_first_event_is_handed_straight_to_the_store(
    inner: CountingStore,
) -> None:
    """Only streams are remembered. A search crosses streams and is not one."""

    once = ReadOnceEventStore(inner)

    found = await once.find_aggregate_ids_by_first_event(
        aggregate_type=PROFILE, payload_equals={"player_id": str(ALICE)}
    )
    await once.find_aggregate_ids_by_first_event(
        aggregate_type=PROFILE, payload_equals={"player_id": str(ALICE)}
    )

    assert found == [ALICE]
    assert len(inner.searches) == 2


async def test_which_streams_exist_is_asked_of_the_store_and_sees_an_append(
    inner: CountingStore,
) -> None:
    """Only streams are remembered. *Which of these exist* is a batch question,
    asked of the store every time — so a stream remembered as absent and then
    appended to through the wrapper is present in the next answer."""

    once = ReadOnceEventStore(inner)
    assert await once.load_stream(aggregate_type=RATING, aggregate_id=BOB) == []
    await once.append(
        aggregate_type=RATING,
        aggregate_id=BOB,
        expected_version=0,
        events=[Happened()],
    )

    first = await once.streams_present(
        aggregate_type=RATING, aggregate_ids=[ALICE, BOB, uuid4()]
    )
    second = await once.streams_present(aggregate_type=PROFILE, aggregate_ids=[BOB])

    assert first == {ALICE, BOB}
    assert second == frozenset()
    assert [kind for kind, _ in inner.presences] == [RATING, PROFILE]


async def test_a_batch_of_loads_is_asked_of_the_store_and_sees_an_append(
    inner: CountingStore,
) -> None:
    """A batch is one statement already (#814): handed to the store every time
    and remembered nowhere, so an append through the wrapper is in the next
    batch."""

    once = ReadOnceEventStore(inner)
    first = await once.load_streams(aggregate_type=RATING, aggregate_ids=[ALICE, BOB])
    await once.append(
        aggregate_type=RATING,
        aggregate_id=BOB,
        expected_version=0,
        events=[Happened()],
    )
    second = await once.load_streams(aggregate_type=RATING, aggregate_ids=[ALICE, BOB])

    assert set(first) == {ALICE}
    assert set(second) == {ALICE, BOB}
    assert inner.batches == [(RATING, (ALICE, BOB)), (RATING, (ALICE, BOB))]
    assert inner.loads == []
