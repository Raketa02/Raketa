"""Domain events infrastructure.

Layout (read in this order to understand the flow):

- `base`      — `DomainEvent` protocol + `EventRecorder` (aggregate-side)
- `registry`  — class ↔ name mapping + JSON-safe (de)serialization
- `bus`       — `EventBus` port + `InProcessEventBus` adapter (subscribers)
- `outbox`    — `OutboxRecord` + `OutboxRepository` port
- `publisher` — `DomainEventPublisher` port + adapters (outbox / direct / noop)
- `relay`     — `OutboxRelay`: drains outbox, dispatches via bus

The application layer depends only on `DomainEventPublisher`. The choice of
adapter (outbox vs direct vs noop) is made by composition root.
"""

from app.shared.events.base import DomainEvent, EventRecorder
from app.shared.events.bus import (
    DispatchResult,
    EventBus,
    EventHandler,
    InProcessEventBus,
)
from app.shared.events.outbox import OutboxRecord, OutboxRepository
from app.shared.events.publisher import (
    DirectDispatchPublisher,
    DomainEventPublisher,
    NoOpDomainEventPublisher,
    OutboxEventPublisher,
)
from app.shared.events.registry import EventRegistry
from app.shared.events.relay import OutboxRelay

__all__ = [
    "DispatchResult",
    "DirectDispatchPublisher",
    "DomainEvent",
    "DomainEventPublisher",
    "EventBus",
    "EventHandler",
    "EventRecorder",
    "EventRegistry",
    "InProcessEventBus",
    "NoOpDomainEventPublisher",
    "OutboxEventPublisher",
    "OutboxRecord",
    "OutboxRelay",
    "OutboxRepository",
]
