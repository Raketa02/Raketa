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

**Three connection pools, opened unconditionally and closed here.** The database
engine and the two Redis clients are the process's, so all three are opened
before anything that might want one and disposed in the same `finally`, after
every background task has stopped — a job still running against a closed pool is
the same shutdown bug in any of them. **None is gated on a feature flag**, and
the Redis ones especially must not be: a request path resolves its ledgers
through the command client, so a job's toggle deciding whether the pool exists
would be a job's toggle deciding whether a Play surface 500s. Opening one
connects to nothing, so a store that is down costs the ledgers their answers and
never costs the application its start (``matchmaking/domain/ledgers.py``).

**The second Redis client is the subscriber's, and it is a second client rather
than a flag** (``docs/adr/0147`` §5, #342). A conversation stream subscribes on
it, and a blocking read with no deadline has no business in the pool a player's
critical path draws its commands from. It is opened here for the same reason the
first is: an open stream must not be the thing that decides a pool exists.

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
    build_nudge_publisher,
    build_scoring_meter,
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
from app.infrastructure.redis_client import (
    close_redis,
    close_redis_subscriber,
    get_redis,
    get_redis_subscriber,
    init_redis,
    init_redis_subscriber,
)

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
        # The other pool, on the same terms and in the same place. It opens no
        # socket — `redis-py` connects on the first command — so this cannot
        # fail here whatever state the store is in.
        init_redis(settings)
        # And the third, which is the subscriber's own. Same terms, same place,
        # and the same lazy connect; what differs is the read deadline, which it
        # does not have (#342).
        init_redis_subscriber(settings)

        # Every piece of background work that touches the database takes a
        # session per tick, so one factory serves all of them — and it is built
        # only if something wants one, which is what lets an application with
        # all of it disabled start without an engine having been reached for at
        # all. **The exposure roll is the first job that wants none**, so the
        # engine is no longer a precondition for having any jobs.
        background: list[BackgroundTask] = []
        # Assigned whether or not anything is registered: an attribute that only
        # sometimes exists is one every reader has to guard against.
        app.state.scheduled_jobs = []
        # Likewise. **One per process, and this is where the one lives**
        # (``docs/adr/0112``): the refresh loop rebuilds it and a search binds a
        # container from it, so a second instance anywhere would be a second
        # index that nothing keeps in step with the first.
        app.state.candidate_source = None
        # Likewise, and unconditionally — trigger 1 is stated *on one worker*
        # (``scale-posture.md`` §4), so the histogram is this process's own and
        # a second instance anywhere would be a second window that nothing
        # closes. It is built whether or not the probe that reads it is
        # registered: the searches are what fill it, and a search may not have
        # to ask whether an instrument exists.
        app.state.scoring_meter = build_scoring_meter()
        # Likewise — one connection pool, and this is where the one lives. It
        # is whatever `init_redis` above returned, unconditionally: the roll is
        # one reader of the ledgers and the Play surfaces are the rest, so this
        # attribute may not depend on the roll being switched on.
        app.state.redis = get_redis()
        # Likewise, and for the same reason: an open conversation stream takes a
        # `PubSub` off this one, so it may not depend on any toggle either.
        app.state.redis_subscriber = get_redis_subscriber()

        session_factory = None
        if (
            settings.EVENT_DELIVERY_WORKER_ENABLED
            or settings.PHOTO_SWEEP_ENABLED
            or settings.CANDIDATE_INDEX_ENABLED
            or settings.INTEREST_EXPIRY_ENABLED
            or settings.CHALLENGE_LAPSE_ENABLED
            or settings.RATING_CATCH_UP_ENABLED
        ):
            session_factory = build_background_session_factory(get_engine())

            if settings.EVENT_DELIVERY_WORKER_ENABLED:
                worker = build_event_delivery_worker(
                    event_runtime=app.state.event_runtime,
                    session_factory=session_factory,
                    settings=settings,
                    # **This is the delivery that is live.** The room teller runs
                    # inside this loop, so a system line written here reaches an
                    # open conversation without anybody refreshing. A seed run
                    # and a command-line drain pass `NobodyIsFollowing` instead,
                    # and the parameter is required so the difference is written
                    # down rather than defaulted.
                    nudges=build_nudge_publisher(app.state.redis),
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
            redis_client=app.state.redis,
            meter=app.state.scoring_meter,
        )
        # Only the scheduled jobs, not the outbox drain beside them: this
        # attribute is what somebody reads to answer *which jobs is this process
        # running*, and an answer that quietly included a queue drain would be a
        # different question's answer.
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
            # After the engine and after every task, for the reason the engine
            # is after the tasks: a pool closed under something still using it
            # turns a clean shutdown into an exception nobody reads.
            await close_redis()
            await close_redis_subscriber()

    return lifespan
