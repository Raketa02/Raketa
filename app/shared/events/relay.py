from __future__ import annotations

import logging

from app.shared.clock import Clock
from app.shared.events.bus import EventBus
from app.shared.events.outbox import OutboxRepository
from app.shared.events.registry import EventRegistry

logger = logging.getLogger(__name__)


class OutboxRelay:
    """Drains the outbox: fetches unpublished records, hydrates them back
    into typed domain events, dispatches via the bus, and marks them
    published. Failures bump an attempt counter and stash the error so the
    next poll cycle retries (at-least-once semantics).
    """

    def __init__(
        self,
        outbox: OutboxRepository,
        bus: EventBus,
        registry: EventRegistry,
        clock: Clock,
        *,
        batch_size: int = 100,
    ) -> None:
        self._outbox = outbox
        self._bus = bus
        self._registry = registry
        self._clock = clock
        self._batch_size = batch_size

    async def relay_once(self) -> int:
        """Process one batch. Returns the number of records successfully
        published. Caller drives the loop / scheduling."""
        records = await self._outbox.fetch_pending(batch_size=self._batch_size)
        published = 0
        for record in records:
            try:
                event = self._registry.deserialize(record.event_type, record.payload)
            except LookupError as exc:
                await self._outbox.mark_failed(
                    record.id,
                    error=f"deserialize failed: {exc}",
                    attempts=record.attempts + 1,
                )
                continue

            result = await self._bus.dispatch(event)
            if result.ok:
                await self._outbox.mark_published(record.id, at=self._clock.now())
                published += 1
            else:
                await self._outbox.mark_failed(
                    record.id,
                    error="; ".join(repr(e) for e in result.errors),
                    attempts=record.attempts + 1,
                )
        return published
