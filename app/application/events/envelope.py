from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class DeliveryContext:
    event_id: UUID
    attempt: int
    occurred_at: datetime


@dataclass(frozen=True)
class SerializedEventEnvelope:
    id: UUID
    event_type: str
    schema_version: int
    payload: dict[str, Any]
    occurred_at: datetime
    attempts: int = 0
    published_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime | None = None
