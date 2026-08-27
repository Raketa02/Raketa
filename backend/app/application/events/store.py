from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.shared.domain import DomainEvent


class EventStreamVersionConflict(RuntimeError):
    """Raised when appending events to a stream with a stale expected version."""


@dataclass(frozen=True)
class StoredDomainEvent:
    """One row of the log, as a reader sees it.

    ``version`` orders this event within its own stream. ``sequence_no`` orders
    it within the whole store and is the only field here that does — see
    ``EventStoreORM``. ``occurred_at`` is the domain moment and may be shared by
    several events, so it is not a tie-break.
    """

    id: UUID
    aggregate_type: str
    aggregate_id: UUID
    version: int
    event: DomainEvent
    occurred_at: datetime
    sequence_no: int
    created_at: datetime | None = None
