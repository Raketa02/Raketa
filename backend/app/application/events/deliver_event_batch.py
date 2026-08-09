from __future__ import annotations

from app.application.events.dispatcher import EventDispatcher
from app.application.events.envelope import DeliveryContext
from app.application.ports.events import EventCodec, PendingOutbox
from app.shared.clock import Clock


class EventBatch:
    """Application workflow for delivering one batch of unpublished domain events."""

    def __init__(
        self,
        *,
        outbox: PendingOutbox,
        codec: EventCodec,
        dispatcher: EventDispatcher,
        clock: Clock,
        batch_size: int = 100,
    ) -> None:
        self._outbox = outbox
        self._codec = codec
        self._dispatcher = dispatcher
        self._clock = clock
        self._batch_size = batch_size

    async def execute(self, *, worker_id: str) -> int:
        records = await self._outbox.fetch_pending(batch_size=self._batch_size)
        published = 0
        for record in records:
            attempt = record.attempts + 1
            try:
                event = self._codec.decode(record)
            except Exception as exc:
                await self._outbox.mark_failed(
                    record.id,
                    error=f"decode failed: {exc}",
                    attempts=attempt,
                )
                continue

            result = await self._dispatcher.dispatch(
                event,
                DeliveryContext(
                    event_id=record.id,
                    attempt=attempt,
                    occurred_at=record.occurred_at,
                ),
            )
            if result.ok:
                await self._outbox.mark_published(record.id, at=self._clock.now())
                published += 1
                continue

            error = "; ".join(repr(exc) for exc in result.errors)
            await self._outbox.mark_failed(
                record.id,
                error=error,
                attempts=attempt,
            )
        return published
