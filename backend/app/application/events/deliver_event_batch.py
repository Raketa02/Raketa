from __future__ import annotations

from app.application.events.dispatcher import EventDispatcher
from app.application.events.envelope import DeliveryContext
from app.application.ports.events import EventCodec, PendingOutbox
from app.application.ports.unit_of_work import UnitOfWork
from app.kernel import Clock


class EventBatch:
    """Application workflow for delivering one batch of unpublished domain events.

    **A handler that writes commits with the row that told it to.** Every
    subscriber was a logger until the Conversation context arrived
    (``docs/adr/0146`` §5), so this loop's transactional posture had never been
    exercised: ``mark_published`` and ``mark_failed`` each commit the session the
    handlers ran in, which means a handler's writes land with the ``published_at``
    that says they were delivered — and, without the rollback below, **a failed
    handler's half-written work would land with the failure mark instead.**

    So the rule is stated once, here, rather than remembered by each subscriber:
    a delivery that succeeded is committed with its mark, and a delivery that
    raised is rolled back **before** the attempt is recorded. Delivery stays
    at-least-once either way — a crash between a handler's write and its mark
    redelivers the event — so a subscriber that writes must still be idempotent,
    and this does not pretend otherwise.
    """

    def __init__(
        self,
        *,
        outbox: PendingOutbox,
        codec: EventCodec,
        dispatcher: EventDispatcher,
        uow: UnitOfWork,
        clock: Clock,
        batch_size: int = 100,
    ) -> None:
        self._outbox = outbox
        self._codec = codec
        self._dispatcher = dispatcher
        self._uow = uow
        self._clock = clock
        self._batch_size = batch_size

    async def execute(self, *, worker_id: str) -> int:
        records = await self._outbox.fetch_pending(batch_size=self._batch_size)
        published = 0
        for record in records:
            # The fetch's locks went with the first commit: another deliverer
            # may hold this one now, or have published it.
            if not await self._outbox.claim(record.id):
                continue
            attempt = record.attempts + 1
            try:
                event = self._codec.decode(record)
            except Exception as exc:
                await self._uow.rollback()
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

            # **Before the mark, not after.** The handlers ran in this
            # session; anything half-written by one that raised must not be
            # committed by the update that records the attempt.
            await self._uow.rollback()
            error = "; ".join(repr(exc) for exc in result.errors)
            await self._outbox.mark_failed(
                record.id,
                error=error,
                attempts=attempt,
            )
        return published
