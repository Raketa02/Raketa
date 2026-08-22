import asyncio
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.events.deliver_event_batch import EventBatch
from app.application.ports.tick import TickWork
from app.infrastructure.events.event_delivery_worker import (
    EventWorker,
)


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


@pytest.mark.asyncio
async def test_the_tick_also_takes_due_match_wakes(session_factory):
    """ADR-0076's second lookup, on the interval the outbox already runs.

    *"No new interval and no second process"* — so the assertion is that both
    ran under one `worker_id`, and not that a timekeeper exists somewhere.
    """

    both = asyncio.Event()
    ran: list[str] = []

    class _Job:
        def __init__(self, name: str) -> None:
            self._name = name

        async def execute(self, *, worker_id: str) -> int:
            ran.append(f"{self._name}@{worker_id}")
            if len(ran) >= 2:
                both.set()
            return 0

    worker = EventWorker(
        session_factory=session_factory,
        batch_factory=lambda _s: cast(EventBatch, _Job("outbox")),
        wake_batch_factory=lambda _s: cast(TickWork, _Job("wakes")),
        poll_interval_seconds=30,
        worker_id="worker-test",
    )
    worker.start()
    await asyncio.wait_for(both.wait(), timeout=1)
    await worker.stop()

    assert ran == ["outbox@worker-test", "wakes@worker-test"]


@pytest.mark.asyncio
async def test_a_failing_outbox_does_not_stop_the_wakes(session_factory):
    """Two guards, not one. A stuck outbox must not hold a club's court: the
    outbox carries a change out of the building, and a wake only ever looks."""

    looked = asyncio.Event()

    class _Broken:
        async def execute(self, *, worker_id: str) -> int:
            raise RuntimeError("the outbox is having a bad day")

    class _Wakes:
        async def execute(self, *, worker_id: str) -> int:
            looked.set()
            return 0

    worker = EventWorker(
        session_factory=session_factory,
        batch_factory=lambda _s: cast(EventBatch, _Broken()),
        wake_batch_factory=lambda _s: cast(TickWork, _Wakes()),
        poll_interval_seconds=30,
        worker_id="worker-test",
    )
    worker.start()
    await asyncio.wait_for(looked.wait(), timeout=1)
    await worker.stop()


@pytest.mark.asyncio
async def test_a_worker_with_no_timekeeper_still_polls(session_factory):
    """The wake factory is optional: `None` is *unwired*, never *an empty tick*."""

    polled = asyncio.Event()

    class _Batch:
        async def execute(self, *, worker_id: str) -> int:
            polled.set()
            return 0

    worker = EventWorker(
        session_factory=session_factory,
        batch_factory=lambda _s: cast(EventBatch, _Batch()),
        poll_interval_seconds=30,
        worker_id="worker-test",
    )
    worker.start()
    await asyncio.wait_for(polled.wait(), timeout=1)
    await worker.stop()
