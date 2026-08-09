from __future__ import annotations

import asyncio
import logging
import socket
from collections.abc import Callable
from contextlib import suppress

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.events.deliver_event_batch import EventBatch
from app.shared.ids import new_uuid

logger = logging.getLogger(__name__)

EventBatchFactory = Callable[[AsyncSession], EventBatch]


class EventWorker:
    """Runs durable event delivery as a background task hosted by the API."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        batch_factory: EventBatchFactory,
        poll_interval_seconds: float = 1.0,
        worker_id: str | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._batch_factory = batch_factory
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
