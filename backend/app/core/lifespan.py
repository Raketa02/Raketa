"""What the API starts beside itself, and what it stops on the way out.

Two kinds of background work, and they are deliberately started the same way and
stopped in the same `finally` (``docs/adr/0092``): the outbox drain, which is a
queue emptied as fast as it fills, and the scheduled jobs, which run because a
period elapsed. Both are ``asyncio`` tasks in this process — the platform owns no
scheduler and no second deployable — so both live and die with the application
that hosts them.

**Everything started here is stopped here.** A background task the shutdown path
forgets is one that holds a database connection open past `dispose_engine`, and
the symptom is a container that takes its whole grace period to die rather than
anything that looks like a bug.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bootstrap.events import build_event_delivery_worker
from app.bootstrap.jobs import build_scheduled_jobs
from app.core.config import Settings
from app.infrastructure.database.engine import (
    dispose_engine,
    get_engine,
    init_engine,
)
from app.infrastructure.jobs import BackgroundTask

logger = logging.getLogger(__name__)


def build_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        init_engine(settings)

        # Every piece of background work takes a session per tick, so one factory
        # serves all of them — and it is built only if something wants one, which
        # is what lets an application with all of it disabled start without an
        # engine having been reached for at all.
        background: list[BackgroundTask] = []
        # Assigned whether or not anything is registered: an attribute that only
        # sometimes exists is one every reader has to guard against.
        app.state.scheduled_jobs = []

        if settings.EVENT_DELIVERY_WORKER_ENABLED or settings.PHOTO_SWEEP_ENABLED:
            session_factory = async_sessionmaker(
                get_engine(), expire_on_commit=False, autoflush=False
            )

            if settings.EVENT_DELIVERY_WORKER_ENABLED:
                worker = build_event_delivery_worker(
                    event_runtime=app.state.event_runtime,
                    session_factory=session_factory,
                    settings=settings,
                )
                # Kept on the application because the delivery worker's identity
                # is the lease its batches claim outbox rows under, and a test or
                # an operator may want to reach it.
                app.state.event_delivery_worker = worker
                background.append(worker)

            jobs = build_scheduled_jobs(
                session_factory=session_factory, settings=settings
            )
            # Only the scheduled jobs, not the outbox drain beside them: this
            # attribute is what somebody reads to answer *which jobs is this
            # process running*, and an answer that quietly included a queue
            # drain would be a different question's answer.
            app.state.scheduled_jobs = jobs
            background.extend(jobs)

        for task in background:
            task.start()

        try:
            yield
        finally:
            # Reversed, so the first thing started is the last thing stopped.
            # Each `stop` is guarded on its own: the engine must not be disposed
            # under a task still using it, so one that refuses to stop may not
            # take the others — or the disposal — down with it.
            for task in reversed(background):
                try:
                    await task.stop()
                except Exception:
                    logger.exception(
                        "background task did not stop cleanly",
                        extra={"job": task.name},
                    )
            await dispose_engine()

    return lifespan
