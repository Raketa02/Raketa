from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.events.sqlalchemy_outbox_repository import (
    SqlAlchemyOutboxRepository,
)
from app.shared.clock import Clock
from app.shared.events import EventBus, EventRegistry, OutboxRelay

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AsyncSession]


class OutboxProcessor:
    """Background task that polls the outbox and drains it via the relay.

    Run as a long-lived asyncio task started in the FastAPI lifespan. Owns
    its own SQLAlchemy session per tick — it must not share a session with
    request handlers since they run in their own transaction scopes.

    The poll interval is intentionally cheap: rows already get an immediate
    pickup signal at the next tick, and `SELECT ... FOR UPDATE SKIP LOCKED`
    makes horizontal scaling safe.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        bus: EventBus,
        registry: EventRegistry,
        clock: Clock,
        *,
        poll_interval_seconds: float = 1.0,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._bus = bus
        self._registry = registry
        self._clock = clock
        self._poll_interval = poll_interval_seconds
        self._batch_size = batch_size
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is not None:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="outbox-processor")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._task, timeout=5.0)
        except asyncio.TimeoutError:
            self._task.cancel()
        finally:
            self._task = None

    async def _run(self) -> None:
        logger.info("outbox-processor started")
        try:
            while not self._stop_event.is_set():
                try:
                    await self._tick()
                except Exception:
                    logger.exception("outbox-processor tick failed")
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), timeout=self._poll_interval
                    )
                except asyncio.TimeoutError:
                    pass
        finally:
            logger.info("outbox-processor stopped")

    async def _tick(self) -> None:
        async with self._session_factory() as session:
            repo = SqlAlchemyOutboxRepository(session) ##???
            relay = OutboxRelay(
                outbox=repo,
                bus=self._bus,
                registry=self._registry,
                clock=self._clock,
                batch_size=self._batch_size,
            )
            await relay.relay_once()
