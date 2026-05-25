from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from app.shared.clock import Clock
from app.shared.events.base import DomainEvent
from app.shared.events.bus import EventBus
from app.shared.events.outbox import OutboxRecord, OutboxRepository
from app.shared.events.registry import EventRegistry
from app.shared.ids import new_uuid


class DomainEventPublisher(Protocol):
    """Application-layer port. The use case calls `publish_many` after an
    aggregate state transition but BEFORE `UnitOfWork.commit()` so that the
    publisher implementation (typically the outbox) participates in the same
    transaction as the aggregate write."""

    async def publish(self, event: DomainEvent) -> None: ...

    async def publish_many(self, events: Iterable[DomainEvent]) -> None: ...


class NoOpDomainEventPublisher:
    """Drops every event. Intended only for tests that deliberately ignore
    side-effects of domain events. Not safe for production use — it pretends
    delivery succeeded without persisting or dispatching anything."""

    async def publish(self, event: DomainEvent) -> None:
        return None

    async def publish_many(self, events: Iterable[DomainEvent]) -> None:
        # Drain the iterable so callers passing a generator don't observe
        # different behaviour from callers passing a list.
        for _ in events:
            pass


class OutboxEventPublisher:
    """Persists events into the outbox table as part of the active SQL
    transaction. Delivery is handled later by the OutboxRelay.

    This implements the canonical transactional-outbox pattern: by writing
    the event in the same DB transaction as the aggregate, we make event
    durability atomic with the state change that produced it.
    """

    def __init__(
        self,
        outbox: OutboxRepository,
        registry: EventRegistry,
        clock: Clock,
    ) -> None:
        self._outbox = outbox
        self._registry = registry
        self._clock = clock

    async def publish(self, event: DomainEvent) -> None:
        await self.publish_many([event])

    async def publish_many(self, events: Iterable[DomainEvent]) -> None:
        records = [
            OutboxRecord(
                id=new_uuid(),
                event_type=self._registry.name_for(type(event)),
                payload=self._registry.serialize(event),
                occurred_at=event.occurred_at,
            )
            for event in events
        ]
        if records:
            await self._outbox.add_many(records)


class DirectDispatchPublisher:
    """Bypasses the outbox and dispatches to the bus in-process.

    Useful for tests where you want to assert side-effects synchronously
    without exercising the outbox-and-relay machinery. NOT recommended for
    production: a publish failure here cannot be recovered if the calling
    transaction has already committed.
    """

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus

    async def publish(self, event: DomainEvent) -> None:
        await self._bus.dispatch(event)

    async def publish_many(self, events: Iterable[DomainEvent]) -> None:
        for event in events:
            await self._bus.dispatch(event)
