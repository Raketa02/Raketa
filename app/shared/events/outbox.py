from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Protocol
from uuid import UUID


@dataclass
class OutboxRecord:
    """Domain representation of a single pending event in the outbox.

    Persistence-agnostic on purpose: the SQLAlchemy adapter maps between this
    and the `event_outbox` table.
    """

    id: UUID
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime
    attempts: int = 0
    published_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: Optional[datetime] = field(default=None)


class OutboxRepository(Protocol):
    """Persistence port for the outbox. The `add` variant runs inside the
    same transaction as the originating aggregate (atomic write). The poll /
    mark variants are used by the background relay."""

    async def add_many(self, records: Iterable[OutboxRecord]) -> None: ...

    async def fetch_pending(self, *, batch_size: int) -> list[OutboxRecord]: ...

    async def mark_published(self, record_id: UUID, *, at: datetime) -> None: ...

    async def mark_failed(
        self, record_id: UUID, *, error: str, attempts: int
    ) -> None: ...
