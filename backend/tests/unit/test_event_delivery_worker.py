import asyncio
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.events.deliver_event_batch import EventBatch
from app.infrastructure.events.event_delivery_worker import (
    JOB_NAME,
    EventWorker,
)
from app.infrastructure.jobs import BackgroundTask


@pytest.mark.asyncio
async def test_event_delivery_worker_starts_delivers_a_batch_and_stops(session_factory):
    delivered = asyncio.Event()
    seen_worker_ids: list[str] = []

    class _Batch:
        async def execute(self, *, worker_id: str) -> int:
            seen_worker_ids.append(worker_id)
            delivered.set()
            return 0

    def build_batch(_session: AsyncSession) -> EventBatch:
        return cast(EventBatch, _Batch())

    worker = EventWorker(
        session_factory=session_factory,
        batch_factory=build_batch,
        poll_interval_seconds=30,
        worker_id="worker-test",
    )
    worker.start()
    await asyncio.wait_for(delivered.wait(), timeout=1)
    await worker.stop()

    assert seen_worker_ids == ["worker-test"]


def test_the_worker_is_what_the_lifespan_starts_and_stops(session_factory):
    """It satisfies `BackgroundTask` — including the `name` the shutdown path
    logs when something does not stop cleanly. Before it had one, that log line
    read `EventWorker` while every job beside it read its real name."""

    worker = EventWorker(
        session_factory=session_factory,
        batch_factory=lambda session: cast(EventBatch, object()),
    )

    assert isinstance(worker, BackgroundTask)
    assert worker.name == JOB_NAME
