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

**One thing here starts nothing and is a refusal.** The matcher's ruleset is
validated before anything else runs, so that a malformed one **fails the deploy**
rather than serving — with an embedded ruleset there is no hot reload to fall
back through, so *the previous one keeps serving* means the old pods are still up
(``docs/adr/0119``). It never falls back to defaults, because a matcher that
silently falls back is one that quietly A/B tests against itself.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.bootstrap.composition import (
    build_background_session_factory,
    build_candidate_source,
)
from app.bootstrap.events import build_event_delivery_worker
from app.bootstrap.jobs import build_scheduled_jobs
from app.bootstrap.matchmaking import verify_ruleset
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
        # Before the database, before any background work: a ruleset that cannot
        # be believed must stop this process rather than start beside it. It
        # reads no setting and takes no argument from here — the four
        # environments run the same numbers.
        verify_ruleset()

        init_engine(settings)

        # Every piece of background work takes a session per tick, so one factory
        # serves all of them — and it is built only if something wants one, which
        # is what lets an application with all of it disabled start without an
        # engine having been reached for at all.
        background: list[BackgroundTask] = []
        # Assigned whether or not anything is registered: an attribute that only
        # sometimes exists is one every reader has to guard against.
        app.state.scheduled_jobs = []
        # Likewise. **One per process, and this is where the one lives**
        # (``docs/adr/0112``): the refresh loop rebuilds it and a search binds a
        # container from it, so a second instance anywhere would be a second
        # index that nothing keeps in step with the first.
        app.state.candidate_source = None

        if (
            settings.EVENT_DELIVERY_WORKER_ENABLED
            or settings.PHOTO_SWEEP_ENABLED
            or settings.CANDIDATE_INDEX_ENABLED
        ):
            session_factory = build_background_session_factory(get_engine())

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

            if settings.CANDIDATE_INDEX_ENABLED:
                app.state.candidate_source = build_candidate_source(
                    session_factory=session_factory
                )

            jobs = build_scheduled_jobs(
                session_factory=session_factory,
                settings=settings,
                candidate_source=app.state.candidate_source,
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
