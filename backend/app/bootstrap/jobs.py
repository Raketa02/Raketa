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

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_candidate_index_tail,
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_exposure_ledger,
    build_photo_storage,
    build_player_profile_repository,
    build_roll_exposure,
)
from app.core.config import Settings
from app.infrastructure.jobs import PeriodicJob
from app.kernel import Clock
from app.modules.matchmaking.domain.index_staleness import (
    freshness_of,
    misses_refresh_target,
)
from app.modules.matchmaking.infrastructure.candidate_snapshot_source import (
    DatabaseCandidateSource,
)
from app.modules.player_profile.application.sweep_uncommitted_photos import (
    SweepUncommittedPhotos,
)

logger = logging.getLogger(__name__)

#: The sweep's name in the logs and on its asyncio task.
PHOTO_SWEEP_JOB = "uncommitted-photo-sweep"

#: The candidate index's two loops. They are **not** one job with two phases:
#: the tail reader writes the shared tables and is safe beside itself because a
#: single cursor row serialises it, while the refresh is **per worker by
#: design** — the one place ``docs/adr/0092``'s *N processes, N runs* is the
#: behaviour wanted rather than the cost paid.
CANDIDATE_INDEX_TAIL_JOB = "candidate-index-tail"
CANDIDATE_INDEX_REFRESH_JOB = "candidate-index-refresh"

#: The exposure roll's name in the logs and on its asyncio task.
EXPOSURE_ROLL_JOB = "exposure-roll"


def build_scheduled_jobs(
    *,
    session_factory: async_sessionmaker[AsyncSession] | None,
    settings: Settings,
    candidate_source: DatabaseCandidateSource | None = None,
    redis_client: Redis | None = None,
) -> list[PeriodicJob]:
    """Every job this process should run, in the order they were registered.

    A list rather than a single object, so adding the next one is appending a
    line here and changing nothing in the lifespan that starts them.

    ``candidate_source`` is passed in rather than built here because it is the
    **one** piece of state a job owns that something else will read: a search
    binds a container from it, so the process must hold exactly one and the
    lifespan is where that one is kept. Absent, the refresh loop is simply not
    registered — a process with no index to serve from has nothing to refresh.

    ``redis_client`` arrives the same way and for the same reason: the process
    holds one connection pool and the lifespan owns it. Unlike
    ``candidate_source`` its absence is **not** a legitimate state — the pool is
    opened unconditionally — so omitting it while the roll is enabled raises.

    ``session_factory`` is optional because **the exposure roll is the first job
    here that wants none** — its whole input and output are in the ephemeral
    store. It is still required by every job that reads the database, and
    omitting it while one of those is enabled raises rather than quietly
    registering nothing.
    """

    jobs: list[PeriodicJob] = []
    if settings.PHOTO_SWEEP_ENABLED or settings.CANDIDATE_INDEX_ENABLED:
        if session_factory is None:
            # Loudly, rather than by registering nothing. *The sweep is off* and
            # *the sweep was enabled and silently dropped* are two states with
            # one symptom — orphans accumulating — and only one of them is
            # somebody's decision. The lifespan builds a factory for exactly
            # these flags, so reaching here is a wiring error and not a
            # configuration one.
            raise ValueError(
                "a job that reads the database is enabled, but no session "
                "factory was passed to build_scheduled_jobs"
            )
        if settings.PHOTO_SWEEP_ENABLED:
            jobs.append(
                build_uncommitted_photo_sweep(
                    session_factory=session_factory, settings=settings
                )
            )
        if settings.CANDIDATE_INDEX_ENABLED:
            jobs.append(
                build_candidate_index_tail_job(
                    session_factory=session_factory, settings=settings
                )
            )
            if candidate_source is not None:
                jobs.append(
                    build_candidate_index_refresh_job(
                        source=candidate_source, settings=settings
                    )
                )
    if settings.EXPOSURE_ROLL_ENABLED:
        if redis_client is None:
            # As loud as the session factory above, and for the same reason: the
            # lifespan opens the pool unconditionally, so reaching here is a
            # wiring error rather than a configuration one — and a roll that
            # silently did not register looks exactly like a roll that is off.
            raise ValueError(
                "the exposure roll is enabled, but no redis client was passed "
                "to build_scheduled_jobs"
            )
        jobs.append(build_exposure_roll_job(client=redis_client, settings=settings))
    return jobs


def build_exposure_roll_job(
    *,
    client: Redis,
    settings: Settings,
) -> PeriodicJob:
    """Publish, per sport, what *shown more often than most* means this week.

    **Idempotent and safe beside itself with no lock** (``docs/adr/0092``), and
    for the simplest of the three reasons on this page: it is a **reader** that
    writes one derived scalar. Two runs racing cannot lose an appearance because
    neither of them touches one, and two runs over an unchanged bucket publish
    the identical number. There is nothing to serialise, so nothing is.

    It takes no session. The only thing it reads and the only thing it writes
    are in the ephemeral store, which makes it the first job here that would run
    in a process with no database at all — and the first whose failure mode is
    already handled below it, since the ledger it is handed fails soft.
    """

    roll = build_roll_exposure(build_exposure_ledger(client))

    async def run() -> None:
        report = await roll.execute()
        # Logged at info even when it published nothing, for the reason every
        # loop here is: *the roll ran and the city was quiet* and *the roll did
        # not run* are the two states this has to be tellable apart from
        # outside. ``players_counted`` is what separates a quiet week from a
        # ledger that answered nothing — the one thing a fail-soft port makes
        # invisible everywhere else.
        logger.info(
            "exposure roll finished",
            extra={
                "job": EXPOSURE_ROLL_JOB,
                "exposure_week": report.week.label,
                "players_counted": report.players_counted,
                "thresholds": {
                    sport.value: threshold
                    for sport, threshold in report.thresholds.items()
                },
            },
        )

    return PeriodicJob(
        name=EXPOSURE_ROLL_JOB,
        interval_seconds=settings.EXPOSURE_ROLL_INTERVAL_SECONDS,
        run=run,
    )


def build_candidate_index_tail_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Fold the log into the candidate index, once a second.

    **Idempotent and safe beside itself with no lock** (``docs/adr/0092``): the
    single cursor row is taken ``FOR UPDATE`` for the tick, so a concurrent run
    blocks, then reads the advanced cursor and finds nothing to do. The lock is
    the transaction, so there is nothing to leak behind a dead process and
    nothing to expire mid-run — which is the exact property that let ADR-0092
    refuse leader election.
    """

    tail = build_candidate_index_tail(settings=settings)

    async def run() -> None:
        async with session_factory() as session:
            report = await tail.tick(session)
        # Logged at info even when it did nothing: *the reader ran and found
        # nothing* and *the reader did not run* are the two states this has to
        # be able to tell apart from outside, and a stalled projection is
        # otherwise silent where a stalled outbox is eventually visible as a
        # missing side effect.
        logger.info(
            "candidate index tail",
            extra={
                "job": CANDIDATE_INDEX_TAIL_JOB,
                "events_applied": report.events_applied,
                "rows_moved": report.rows_moved,
                "snapshot_version": report.snapshot_version,
                "waiting_on_hole": report.waiting_on_hole,
            },
        )

    return PeriodicJob(
        name=CANDIDATE_INDEX_TAIL_JOB,
        interval_seconds=settings.CANDIDATE_INDEX_TAIL_INTERVAL_SECONDS,
        run=run,
    )


def build_candidate_index_refresh_job(
    *,
    source: DatabaseCandidateSource,
    settings: Settings,
    clock: Clock | None = None,
) -> PeriodicJob:
    """Rebuild this worker's containers from what moved, every two seconds.

    **Two readings of one lag, and they do different things.** Missing §17's p99
    raises the log level and **changes nothing about what a search does**; the
    ladder's rung is recorded beside it, which is the *internal* half of
    ``index_stale`` — on the structured logs and on the search record, never on
    the wire envelope (``docs/adr/0111``). What the ladder does not do here is
    decide anything: the refusal belongs where a search reads a container, and
    that caller does not exist yet.
    """

    reading = clock or build_clock()

    async def run() -> None:
        report = await source.refresh()
        # The real lag a search would read, not the interval this loop is
        # configured at: what §17 alerts on is *how far behind the log the
        # containers are*, and a loop that reported its own cadence back would
        # be alerting on a constant.
        lag = reading.now() - report.caught_up_at
        missed = misses_refresh_target(lag)
        logger.log(
            # A miss is an **alert**, so it leaves the level every healthy tick
            # writes at. A boolean field on an INFO line is a thing nobody is
            # paged by, which is the same as not raising one.
            logging.WARNING if missed else logging.INFO,
            "candidate index refreshed",
            extra={
                "job": CANDIDATE_INDEX_REFRESH_JOB,
                "snapshot_version": report.snapshot_version,
                "partitions": report.partitions,
                "rows_held": report.rows_held,
                "rows_decoded": report.rows_decoded,
                "index_lag_seconds": lag.total_seconds(),
                "misses_refresh_target": missed,
                # §18's rung, recorded rather than acted on. `index_stale` is
                # this field being anything but FRESH.
                "index_freshness": freshness_of(lag).value,
            },
        )

    return PeriodicJob(
        name=CANDIDATE_INDEX_REFRESH_JOB,
        interval_seconds=settings.CANDIDATE_INDEX_REFRESH_INTERVAL_SECONDS,
        run=run,
    )


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
