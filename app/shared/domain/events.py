from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class DomainEvent(Protocol):
    """Immutable fact recorded by an aggregate during a state transition."""

    @property
    def occurred_at(self) -> datetime: ...


class EventRecorder:
    """Collects events raised by one aggregate until the use case releases them."""

    __slots__ = ("_events",)

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def record(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull(self) -> list[DomainEvent]:
        drained, self._events = self._events, []
        return drained

    def __bool__(self) -> bool:
        return bool(self._events)
