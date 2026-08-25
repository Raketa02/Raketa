"""The outbox drain: the platform's first background job, and now one of two.

**What is here is what makes this job that job** — a session per tick, a batch
built over it, and the worker identity the batch leases its rows under. The loop
around it, the shutdown and the swallowed failure are ``PeriodicJob``'s
(``app/infrastructure/jobs/``), which this delegates to rather than copies.

That split was made when the photo sweep arrived (``docs/adr/0092``), and it is
worth naming why: the two jobs are not the same *kind* of work — this one drains
a queue at one-second intervals, the sweep runs a schedule every few hours — but they
are the same *loop*, and a shutdown path written twice is one that is correct in
one copy and not the other.

**The worker id stays here.** It is not scheduling: it is the lease the outbox
batch claims rows under, so two processes draining the same table do not deliver
the same event twice. A generic loop has no business with it, and the sweep has
no use for one — it needs no lease at all, which is the property that let ADR-0092
avoid a leader election.
"""

from __future__ import annotations

import socket
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.events.deliver_event_batch import EventBatch
from app.infrastructure.jobs import PeriodicJob
from app.shared.ids import new_uuid

#: The job's name in the logs and on the asyncio task.
JOB_NAME = "event-delivery-worker"

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
        self._worker_id = worker_id or f"{socket.gethostname()}:{new_uuid()}"
        self._job = PeriodicJob(
            name=JOB_NAME,
            interval_seconds=poll_interval_seconds,
            run=self._poll_once,
            log_context={"worker_id": self._worker_id},
        )

    @property
    def name(self) -> str:
        return JOB_NAME

    def start(self) -> None:
        self._job.start()

    async def stop(self) -> None:
        await self._job.stop()

    async def _poll_once(self) -> None:
        async with self._session_factory() as session:
            batch = self._batch_factory(session)
            await batch.execute(worker_id=self._worker_id)
