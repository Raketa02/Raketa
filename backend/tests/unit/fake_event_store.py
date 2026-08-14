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
3. **Insertion order is preserved**, because "the newest open run wins" reads the
   candidate scan in reverse.
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
from app.modules.rating.application.event_subscriptions import register_rating_events
from app.shared.domain import DomainEvent


def rating_event_codec() -> JsonEventCodec:
    """The codec the application runs, with this context's events registered."""

    catalog = EventCatalog()
    register_rating_events(catalog)
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


class InMemoryEventStore:
    """Append-only streams held in a dict, keyed as the real store keys them."""

    def __init__(self) -> None:
        self._codec = rating_event_codec()
        # Insertion-ordered: streams in the order they were opened, rows in the
        # order they were appended.
        self._streams: dict[tuple[str, UUID], list[_Row]] = {}
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
            )
            for offset, (event, encoded) in enumerate(
                ((event, self._codec.encode(event)) for event in pending), start=1
            )
        ]
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
        matched: list[UUID] = []
        for (stream_type, aggregate_id), stream in self._streams.items():
            if stream_type != aggregate_type or not stream:
                continue
            opening = stream[0].payload
            if all(opening.get(key) == value for key, value in payload_equals.items()):
                matched.append(aggregate_id)
        return matched

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
