from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import Settings
from app.infrastructure.database.engine import (
    dispose_engine,
    get_engine,
    init_engine,
)
from app.infrastructure.events.outbox_processor import OutboxProcessor
from app.shared.clock import SystemClock


def build_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        init_engine(settings)

        processor: OutboxProcessor | None = None
        if settings.OUTBOX_PROCESSOR_ENABLED:
            session_factory = async_sessionmaker(
                get_engine(), expire_on_commit=False, autoflush=False
            )
            processor = OutboxProcessor(
                session_factory=session_factory,
                bus=app.state.event_bus,
                registry=app.state.event_registry,
                clock=SystemClock(),
                poll_interval_seconds=settings.OUTBOX_POLL_INTERVAL_SECONDS,
                batch_size=settings.OUTBOX_BATCH_SIZE,
            )
            processor.start()
            app.state.outbox_processor = processor

        try:
            yield
        finally:
            if processor is not None:
                await processor.stop()
            await dispose_engine()

    return lifespan
