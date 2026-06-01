from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bootstrap.events import build_event_delivery_worker
from app.core.config import Settings
from app.infrastructure.database.engine import (
    dispose_engine,
    get_engine,
    init_engine,
)
from app.infrastructure.events.event_delivery_worker import (
    EventWorker,
)


def build_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        init_engine(settings)

        worker: EventWorker | None = None
        if settings.EVENT_DELIVERY_WORKER_ENABLED:
            session_factory = async_sessionmaker(
                get_engine(), expire_on_commit=False, autoflush=False
            )
            worker = build_event_delivery_worker(
                event_runtime=app.state.event_runtime,
                session_factory=session_factory,
                settings=settings,
            )
            worker.start()
            app.state.event_delivery_worker = worker

        try:
            yield
        finally:
            if worker is not None:
                await worker.stop()
            await dispose_engine()

    return lifespan
