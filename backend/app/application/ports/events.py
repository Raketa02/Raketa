from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
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

    async def streams_present(
        self, *, aggregate_type: str, aggregate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        """Which of these streams hold at least one event.

        **Addressed, never searched.** The caller names every stream it asks
        about, so this is ``load_stream``'s keyed read for a batch and without
        the events — one statement however many ids, answering only about those.
        A stream that does not exist is absent, which is the same answer as
        ``load_stream``'s empty list with nothing to translate. Empty in, empty
        out, and no statement.

        For a caller that needs *whether*, never *what*: replaying a stream to
        learn that it exists is a load and a fold for one bit.
        """
        ...

    async def find_aggregate_ids_by_first_event(
        self, *, aggregate_type: str, payload_equals: Mapping[str, str]
    ) -> list[UUID]:
        """Ids of streams whose first (version 1) event's payload matches all pairs.

        The read side of an event-sourced index: a stream's opening event carries
        the fields it is keyed by (a player, a sport), so a lookup needs no
        parallel table — it reads the streams directly.

        **Ordered by append order, oldest first** — the position each stream's
        opening event took in the store, not the instant it claims. This is the
        one read in the system that crosses streams, and callers tie-break on the
        order (``_newest_open_by_sport`` scans it in reverse), so the guarantee is
        part of the contract rather than an artefact of the query. Domain time
        cannot supply it: two streams opened in one commit share an
        ``occurred_at``.
        """
        ...


class PendingOutbox(Protocol):
    async def fetch_pending(
        self, *, batch_size: int
    ) -> list[SerializedEventEnvelope]: ...

    async def claim(self, event_id: UUID) -> bool:
        """Hold this event for delivery until the next commit — ``False`` when
        another deliverer holds it or has published it since the batch was read.

        **Asked for every event, not once per batch**, because a batch commits
        once per event: the first commit releases every row its fetch locked,
        and another deliverer may then take the rest."""
        ...

    async def mark_published(self, event_id: UUID, *, at: datetime) -> None: ...

    async def mark_failed(
        self, event_id: UUID, *, error: str, attempts: int
    ) -> None: ...
