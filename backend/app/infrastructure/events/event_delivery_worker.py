from __future__ import annotations

import asyncio
import logging
import socket
from collections.abc import Callable
from contextlib import suppress

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.events.deliver_event_batch import EventBatch
from app.application.ports.tick import TickWork
from app.shared.ids import new_uuid

logger = logging.getLogger(__name__)

EventBatchFactory = Callable[[AsyncSession], EventBatch]
#: Whose work it is stays the composition root's business — the tick only knows
#: it is a bounded slice with a `worker_id` (`app/application/ports/tick.py`).
TickWorkFactory = Callable[[AsyncSession], TickWork]


class EventWorker:
    """The process's one background tick: delivery, the wakes, and the cascade.

    **Three jobs, one interval, and ADR-0076 asks for exactly that** — *"the
    existing `EventWorker` gains two more indexed lookups on the tick it already
    runs: the outbox, due match wakes, due sends. No new interval and no second
    process."* The third is the invitation cascade's dispatch queue (ADR-0061,
    ``Raketa02/Raketa#82``), which is a different queue from the *sends* that
    line anticipates: this one decides **whom to tell**, and the notification
    channel that tells them arrives with ``Raketa02/Raketa#84``.

    The cost is stated rather than discovered: **one worker means one queue of
    work**, so a slow job delays whatever is behind it. Affordable because no
    boundary on this map costs anybody anything if it fires a minute late, and it
    stops being affordable the moment one needs honouring in seconds.

    **Each job gets its own session and its own guard**, so a wake that raises
    cannot roll back a published outbox row and cannot stop the outbox running at
    all. One interval, two units of work — never one unit that fails as a whole.
    """

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        batch_factory: EventBatchFactory,
        wake_batch_factory: TickWorkFactory | None = None,
        cascade_batch_factory: TickWorkFactory | None = None,
        poll_interval_seconds: float = 1.0,
        worker_id: str | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._batch_factory = batch_factory
        self._wake_batch_factory = wake_batch_factory
        self._cascade_batch_factory = cascade_batch_factory
        self._poll_interval = poll_interval_seconds
        self._worker_id = worker_id or f"{socket.gethostname()}:{new_uuid()}"
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is not None:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="event-delivery-worker")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._task, timeout=5.0)
        except asyncio.TimeoutError:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        finally:
            self._task = None

    async def _run(self) -> None:
        logger.info(
            "event-delivery-worker started",
            extra={"worker_id": self._worker_id},
        )
        try:
            while not self._stop_event.is_set():
                try:
                    await self._poll_once()
                except Exception:
                    logger.exception("event-delivery-worker poll failed")
                try:
                    await self._take_due_wakes()
                except Exception:
                    logger.exception("match-wake tick failed")
                try:
                    await self._take_due_dispatches()
                except Exception:
                    logger.exception("cascade tick failed")
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), timeout=self._poll_interval
                    )
                except asyncio.TimeoutError:
                    pass
        finally:
            logger.info(
                "event-delivery-worker stopped",
                extra={"worker_id": self._worker_id},
            )

    async def _poll_once(self) -> None:
        async with self._session_factory() as session:
            batch = self._batch_factory(session)
            await batch.execute(worker_id=self._worker_id)

    async def _take_due_wakes(self) -> None:
        """ADR-0076's second lookup. Absent rather than empty when unwired.

        Second on the tick, and deliberately: the outbox is what carries a change
        out of the building, and a wake only ever *looks*.
        """

        if self._wake_batch_factory is None:
            return
        async with self._session_factory() as session:
            batch = self._wake_batch_factory(session)
            await batch.execute(worker_id=self._worker_id)

    async def _take_due_dispatches(self) -> None:
        """ADR-0061's two dispatch jobs. Absent rather than empty when unwired.

        Last on the tick, and deliberately: the two jobs above it decide what is
        **true** — a court given back, a claim reaped, a result settled — and
        this one decides who is **told**. A dispatch reading a record the wake
        has just moved is a dispatch telling the truth; the other order would
        offer a seat on a match that had cancelled a second earlier.
        """

        if self._cascade_batch_factory is None:
            return
        async with self._session_factory() as session:
            batch = self._cascade_batch_factory(session)
            await batch.execute(worker_id=self._worker_id)
