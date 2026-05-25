from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class DomainEvent(Protocol):
    """Structural contract every domain event must satisfy.

    Events are immutable facts about something that happened in the domain.
    They are recorded on the aggregate that produced them and pulled out by
    the application layer after a successful state transition.
    """

    @property
    def occurred_at(self) -> datetime: ...


class EventRecorder:
    """Owned by an aggregate via composition. Collects events raised during
    a unit of work; the application layer pulls them after commit."""

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
