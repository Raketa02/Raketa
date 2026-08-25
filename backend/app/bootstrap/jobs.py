"""The register of scheduled jobs. **Add the next one here.**

One function per job, each returning a ``PeriodicJob`` built out of
``app/bootstrap/composition.py``'s adapters — so a job reaches the same bucket
and the same event store a request does, rather than a second opinion about
where either lives. Nothing in ``app/infrastructure/jobs/`` knows what any job
does; this module is where *what* meets *how often*.

**A job may only be registered here if it is idempotent and safe to run beside
itself** (``docs/adr/0092``). The mechanism is an ``asyncio`` task in every API
process, so with N processes a job runs N times per interval at unrelated
moments, and there is no lock anywhere. That is a rule about the job, not about
this file, and it is checked by reading rather than by a test — which is why it
is written at the top of the module a new job is added to.

The session is per *run*, not per job: a job that held one open between ticks
would hold a pooled connection for the whole interval. The photo storage is
built once, because it holds no session and opens no connection —
an ``aioboto3.Session`` is credentials and a region.

**Within a run the session is shared, and that has a cost worth naming.** The
sweep's profile replays all go through one session, so a read transaction stays
open while the object store is paged. It is invisible at today's corpus;
``docs/adr/0092`` records what to change when it is not, and why the narrower
port that would fix it is not built yet.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_photo_storage,
    build_player_profile_repository,
)
from app.core.config import Settings
from app.infrastructure.jobs import PeriodicJob
from app.modules.player_profile.application.sweep_uncommitted_photos import (
    SweepUncommittedPhotos,
)

logger = logging.getLogger(__name__)

#: The sweep's name in the logs and on its asyncio task.
PHOTO_SWEEP_JOB = "uncommitted-photo-sweep"


def build_scheduled_jobs(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> list[PeriodicJob]:
    """Every job this process should run, in the order they were registered.

    A list rather than a single object, so adding the second one is appending a
    line here and changing nothing in the lifespan that starts them.
    """

    jobs: list[PeriodicJob] = []
    if settings.PHOTO_SWEEP_ENABLED:
        jobs.append(
            build_uncommitted_photo_sweep(
                session_factory=session_factory, settings=settings
            )
        )
    return jobs


def build_uncommitted_photo_sweep(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Delete photos uploaded and never committed to a profile (#142).

    Idempotent and lock-free by construction — see the use case, which is where
    the argument for both lives.
    """

    storage = build_photo_storage(settings)
    clock = build_clock()

    async def sweep() -> None:
        async with session_factory() as session:
            event_store = build_domain_event_store(session)
            report = await SweepUncommittedPhotos(
                storage=storage,
                profiles=build_player_profile_repository(
                    event_store=event_store,
                    events=build_event_publisher(session),
                ),
                clock=clock,
            ).execute()

        # The job's only output. Logged at info even when it did nothing,
        # because *the sweep ran and found nothing* and *the sweep did not run*
        # are the two states this has to be able to tell apart from outside.
        logger.info(
            "uncommitted photo sweep finished",
            extra={
                "job": PHOTO_SWEEP_JOB,
                "photos_examined": report.examined,
                "photos_deleted": report.deleted,
            },
        )

    return PeriodicJob(
        name=PHOTO_SWEEP_JOB,
        interval_seconds=settings.PHOTO_SWEEP_INTERVAL_SECONDS,
        run=sweep,
    )
