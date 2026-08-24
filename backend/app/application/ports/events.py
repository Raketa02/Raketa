from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.application.events.envelope import SerializedEventEnvelope
from app.application.events.store import StoredDomainEvent
from app.shared.domain import DomainEvent


@dataclass(frozen=True)
class EncodedEvent:
    event_type: str
    schema_version: int
    payload: dict[str, Any]


class EventDecodingError(ValueError):
    """A persisted event cannot be reconstituted into its domain-event class."""


class DomainEventPublisher(Protocol):
    """Queues released domain events in the current use-case transaction."""

    async def publish(self, event: DomainEvent) -> None: ...

    async def publish_many(self, events: Iterable[DomainEvent]) -> None: ...


class EventCodec(Protocol):
    def encode(self, event: DomainEvent) -> EncodedEvent: ...

    def decode(self, envelope: SerializedEventEnvelope) -> DomainEvent: ...


class OutboxWriter(Protocol):
    async def add_many(self, records: Iterable[SerializedEventEnvelope]) -> None: ...


class DomainEventStore(Protocol):
    async def append(
        self,
        *,
        aggregate_type: str,
        aggregate_id: UUID,
        expected_version: int,
        events: Iterable[DomainEvent],
    ) -> list[StoredDomainEvent]: ...

    async def load_stream(
        self, *, aggregate_type: str, aggregate_id: UUID
    ) -> list[StoredDomainEvent]: ...

    async def find_aggregate_ids_by_first_event(
        self, *, aggregate_type: str, payload_equals: Mapping[str, str]
    ) -> list[UUID]:
        """Ids of streams whose first (version 1) event's payload matches all pairs.

        The read side of an event-sourced index: a stream's opening event carries
        the fields it is keyed by (a player, a sport), so a lookup needs no
        parallel table — it reads the streams directly. Ordered by when the stream
        opened, oldest first.
        """
        ...

    async def find_first_event_field(
        self,
        *,
        aggregate_type: str,
        payload_equals: Mapping[str, str],
        field: str,
    ) -> list[str]:
        """One **payload field** of every matching opening event, oldest first.

        The same index read as above pointed at the payload rather than at the
        stream id, and it exists because a derived stream id cannot be reversed.
        A Skill rating's id is ``uuid5(player, sport)``, which makes every
        by-pair read one lookup with no index — and makes *whose rating is this*
        unanswerable from the id alone. Without this, a caller asking **who**
        holds a rating at a sport has to load each matched stream to read its
        first event back, which is one query per player on a question that is
        one query.

        Raw strings, because the store holds a JSON payload and does not know
        that a field spelled like a UUID is one. The caller parses, and a value
        it cannot parse is a payload that has drifted from the event class.
        """
        ...


class PendingOutbox(Protocol):
    async def fetch_pending(
        self, *, batch_size: int
    ) -> list[SerializedEventEnvelope]: ...

    async def mark_published(self, event_id: UUID, *, at: datetime) -> None: ...

    async def mark_failed(
        self, event_id: UUID, *, error: str, attempts: int
    ) -> None: ...
