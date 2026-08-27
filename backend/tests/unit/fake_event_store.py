"""An in-memory ``DomainEventStore``, faithful in the three ways that matter.

Use-case tests fake the **event store**, not the repository. A repository fake
would leave the identity map, the version arithmetic and the encoded lookup keys
— everything the repository introduced — exercised by nothing.

That only works if the double is faithful where the real store's behaviour is
load-bearing, so three rules are deliberate rather than convenient:

1. **The expected version is enforced as equality against the stream's length**,
   which is exactly the real store's semantics: it compares the caller's expected
   version against the stream's current maximum, so an append at a stale version
   raises rather than being reordered or dropped.
2. **Events go through the real codec.** The stream lookups match the *stored
   JSON payload* of a stream's opening event, not Python attributes, so a double
   that skipped encoding would pass a test the real query fails — a renamed field
   would simply return nothing, which is indistinguishable from "no run in
   progress".
3. **Append order is modelled explicitly**, by a store-wide counter rather than
   by dict insertion order. "The newest open run wins" reads the candidate scan
   in reverse, so that order is load-bearing — and the real adapter now gets it
   from a `sequence_no` column rather than from `occurred_at`, which cannot
   order two streams opened in one commit. A double that leaned on Python dict
   ordering would keep passing if the real query lost its ordering guarantee.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.events.catalog import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.application.events.store import (
    EventStreamVersionConflict,
    StoredDomainEvent,
)
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.blocks.application.event_subscriptions import register_block_events
from app.modules.player_profile.application.event_subscriptions import (
    register_player_profile_events,
)
from app.modules.rating.application.event_subscriptions import register_rating_events
from app.shared.domain import DomainEvent


def rating_event_codec() -> JsonEventCodec:
    """The codec the application runs, with the rating context's events only.

    Kept narrow for the tests that are *about* the rating codec — a catalog with
    one context in it is what makes "this event has no contract" a failure those
    tests can assert. The store below uses the whole catalog instead.
    """

    catalog = EventCatalog()
    register_rating_events(catalog)
    return JsonEventCodec(catalog)


def domain_event_codec() -> JsonEventCodec:
    """The codec with every context registered, as the application builds it.

    The fake store uses this rather than one context's, because a store that
    could only encode one module's events would refuse a use case from any other
    — and the refusal would look like a bug in the use case.
    """

    catalog = EventCatalog()
    register_rating_events(catalog)
    register_player_profile_events(catalog)
    register_block_events(catalog)
    return JsonEventCodec(catalog)


@dataclass
class _Row:
    id: UUID
    aggregate_type: str
    aggregate_id: UUID
    version: int
    event_type: str
    schema_version: int
    payload: dict[str, object]
    occurred_at: datetime
    sequence_no: int


class InMemoryEventStore:
    """Append-only streams held in a dict, keyed as the real store keys them."""

    def __init__(self) -> None:
        self._codec = domain_event_codec()
        # Insertion-ordered: streams in the order they were opened, rows in the
        # order they were appended.
        self._streams: dict[tuple[str, UUID], list[_Row]] = {}
        # Stands in for the store's `sequence_no` identity column: one counter
        # for the whole store, so rows on different streams get a defined
        # relative order exactly as the database gives them one.
        self._next_sequence_no = 1
        # Counted so a test can assert the store was never *asked*. An empty
        # append is a no-op here and in the real adapter, so counting rows alone
        # cannot tell "wrote nothing" from "never called".
        self.appends = 0

    async def append(
        self,
        *,
        aggregate_type: str,
        aggregate_id: UUID,
        expected_version: int,
        events: Iterable[DomainEvent],
    ) -> list[StoredDomainEvent]:
        self.appends += 1
        pending = list(events)
        if not pending:
            return []

        stream = self._streams.setdefault((aggregate_type, aggregate_id), [])
        if len(stream) != expected_version:
            raise EventStreamVersionConflict(
                f"Expected {aggregate_type}/{aggregate_id} at version "
                f"{expected_version}, found {len(stream)}"
            )

        rows = [
            _Row(
                id=uuid4(),
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                version=expected_version + offset,
                event_type=encoded.event_type,
                schema_version=encoded.schema_version,
                payload=encoded.payload,
                occurred_at=event.occurred_at,
                sequence_no=self._next_sequence_no + offset - 1,
            )
            for offset, (event, encoded) in enumerate(
                ((event, self._codec.encode(event)) for event in pending), start=1
            )
        ]
        self._next_sequence_no += len(rows)
        stream.extend(rows)
        return [self._to_stored(row) for row in rows]

    async def load_stream(
        self, *, aggregate_type: str, aggregate_id: UUID
    ) -> list[StoredDomainEvent]:
        stream = self._streams.get((aggregate_type, aggregate_id), [])
        return [self._to_stored(row) for row in stream]

    async def find_aggregate_ids_by_first_event(
        self, *, aggregate_type: str, payload_equals: Mapping[str, str]
    ) -> list[UUID]:
        matched: list[tuple[int, UUID]] = []
        for (stream_type, aggregate_id), stream in self._streams.items():
            if stream_type != aggregate_type or not stream:
                continue
            opening = stream[0]
            if all(
                opening.payload.get(key) == value
                for key, value in payload_equals.items()
            ):
                matched.append((opening.sequence_no, aggregate_id))
        # Sorted on the opening event's append position, which is what the real
        # query's `ORDER BY sequence_no` returns. Sorting rather than trusting
        # dict order is the point: it is the guarantee that is being doubled.
        return [aggregate_id for _, aggregate_id in sorted(matched)]

    def _to_stored(self, row: _Row) -> StoredDomainEvent:
        # Decoded on the way out, exactly as the real adapter does, so a payload
        # the codec cannot read fails here too.
        event = self._codec.decode(
            SerializedEventEnvelope(
                id=row.id,
                event_type=row.event_type,
                schema_version=row.schema_version,
                payload=dict(row.payload),
                occurred_at=row.occurred_at,
            )
        )
        return StoredDomainEvent(
            id=row.id,
            sequence_no=row.sequence_no,
            aggregate_type=row.aggregate_type,
            aggregate_id=row.aggregate_id,
            version=row.version,
            event=event,
            occurred_at=row.occurred_at,
        )


class RecordingPublisher:
    """Collects what a use case released, in the order it released it."""

    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.published.append(event)

    async def publish_many(self, events: Iterable[DomainEvent]) -> None:
        self.published.extend(events)


@dataclass
class CountingUnitOfWork:
    """Counts transaction boundaries so a test can assert there was exactly one."""

    commits: int = field(default=0)
    rollbacks: int = field(default=0)
    flushes: int = field(default=0)

    async def commit(self) -> None:
        self.commits += 1

    async def flush(self) -> None:
        self.flushes += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


def utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


@dataclass
class FrozenClock:
    """One instant, so an event's ``occurred_at`` is something a test can name."""

    at: datetime = field(default_factory=lambda: utc(2026, 8, 14))

    def now(self) -> datetime:
        return self.at
