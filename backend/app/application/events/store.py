from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.shared.domain import DomainEvent


class EventStreamVersionConflict(RuntimeError):
    """Raised when appending events to a stream with a stale expected version."""


@dataclass(frozen=True)
class StoredDomainEvent:
    id: UUID
    aggregate_type: str
    aggregate_id: UUID
    version: int
    event: DomainEvent
    occurred_at: datetime
    created_at: datetime | None = None
