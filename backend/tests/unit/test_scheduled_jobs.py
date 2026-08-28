"""The register of scheduled jobs, and the sweep run through its real wiring.

The tracer `test_composition_root.py` describes: a job assembled from the
factories alone — a session factory and the settings, no application and no
request — and then *run*, because a builder that returns an object nobody
exercises proves only that a constructor accepted its arguments.

The object store is the one thing substituted, since the real one is a network
call. Everything else is what production runs: the session comes from the same
factory, the repository is the event-sourced one, and the profile is replayed
out of SQLite.
"""

from __future__ import annotations

import logging
from datetime import timedelta

import pytest
from uuid import UUID

import app.bootstrap.jobs as jobs_module
from app.bootstrap.composition import build_clock
from app.bootstrap.jobs import (
    CANDIDATE_INDEX_REFRESH_JOB,
    CANDIDATE_INDEX_TAIL_JOB,
    EXPOSURE_ROLL_JOB,
    GRID_STALENESS_JOB,
    INTEREST_EXPIRY_JOB,
    INTENT_DRIFT_JOB,
    PHOTO_SWEEP_JOB,
    build_scheduled_jobs,
)
from app.core.config import get_settings
from app.kernel import Sport, instant
from app.modules.matchmaking.domain.ledgers import week_of
from app.modules.matchmaking.infrastructure.redis_ledgers import (
    RedisExposureLedger,
    busy_threshold_key,
)
from app.modules.player_profile.domain.photos import PhotoRef, TranscodedImage
from app.shared.ids import new_uuid
from tests.unit.fake_photo_storage import InMemoryPhotoStorage
from tests.unit.fake_redis import BrokenRedis, FakeRedis

#: Stands in for a session factory a job is built with and never runs against.
#: These cases assert what is *registered*, and the factory is only reached at
#: tick time — the tracers below hand over the real one.
UNUSED_SESSIONS = object()

ALICE = UUID("11111111-1111-1111-1111-111111111111")
IMAGE = TranscodedImage(data=b"jpeg", media_type="image/jpeg", width=10, height=10)


def test_the_sweep_is_registered_and_carries_the_configured_cadence():
    """The cadence is read from the settings and not hard-coded in the job.

    Asserted rather than assumed, because the alternative — a constant in
    `jobs.py` — would leave `PHOTO_SWEEP_INTERVAL_SECONDS` in the templates and
    the README as configuration that changes nothing.
    """

    settings = _nothing_but(
        PHOTO_SWEEP_ENABLED=True, PHOTO_SWEEP_INTERVAL_SECONDS=900.0
    )

    jobs = build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)

    assert [job.name for job in jobs] == [PHOTO_SWEEP_JOB]
    assert jobs[0].interval_seconds == 900.0


def test_a_job_that_is_turned_off_is_not_registered():
    """Off is off — not built and then never started, which would still hold
    whatever its construction reached for."""

    assert build_scheduled_jobs(session_factory=None, settings=_nothing_but()) == []


def test_the_candidate_index_registers_two_loops_and_not_one():
    """The tail writes the shared tables; the refresh rebuilds this worker's own.

    Two jobs rather than one with two phases, because they are safe beside
    themselves for opposite reasons: the tail because a single cursor row taken
    ``FOR UPDATE`` serialises it, the refresh because being **per worker** is the
    behaviour wanted rather than the cost paid (``docs/adr/0092``,
    ``docs/adr/0112``).
    """

    settings = _nothing_but(CANDIDATE_INDEX_ENABLED=True)
    source = object()

    jobs = build_scheduled_jobs(
        session_factory=UNUSED_SESSIONS, settings=settings, candidate_source=source
    )

    assert [job.name for job in jobs] == [
        CANDIDATE_INDEX_TAIL_JOB,
        CANDIDATE_INDEX_REFRESH_JOB,
    ]
    assert [job.interval_seconds for job in jobs] == [1.0, 2.0]


def test_the_refresh_is_not_registered_without_an_index_to_refresh():
    """A process holding no source has nothing to rebuild.

    The tail still runs: writing the tables is shared work and does not depend on
    this process serving a search from them.
    """

    settings = _nothing_but(CANDIDATE_INDEX_ENABLED=True)

    jobs = build_scheduled_jobs(
        session_factory=UNUSED_SESSIONS, settings=settings, candidate_source=None
    )

    assert [job.name for job in jobs] == [CANDIDATE_INDEX_TAIL_JOB]


def test_a_database_job_without_a_session_factory_refuses_to_be_registered():
    """Loudly, rather than by registering nothing.

    *The sweep is off* and *the sweep was enabled and silently dropped* have one
    symptom — orphans accumulating — and only one of them is somebody's
    decision. The parameter went optional when the exposure roll arrived wanting
    no session, which is exactly when that hole opened.
    """

    settings = _nothing_but(PHOTO_SWEEP_ENABLED=True)

    with pytest.raises(ValueError, match="session factory"):
        build_scheduled_jobs(session_factory=None, settings=settings)


def _nothing_but(**overrides):
    """Settings with every job off, so a list of one is a list of one.

    One helper rather than one per job: a second *everything but mine off*
    builder is a second place a newly registered job has to be remembered, and
    forgetting it does not fail — it makes some other job's test assert the
    wrong list.
    """

    return get_settings().model_copy(
        update={
            "PHOTO_SWEEP_ENABLED": False,
            "CANDIDATE_INDEX_ENABLED": False,
            "EXPOSURE_ROLL_ENABLED": False,
            "INTENT_DRIFT_ENABLED": False,
            "GRID_STALENESS_ENABLED": False,
            "INTEREST_EXPIRY_ENABLED": False,
            **overrides,
        }
    )


async def test_the_sweep_job_runs_end_to_end_through_the_real_wiring(
    monkeypatch, session_factory, caplog
):
    """One orphan, one run of the job's own callable, one deleted object.

    What this proves that the use-case tests cannot: the session, the event
    store and the repository are really assembled per run, and the job's
    callable is the thing that does it.
    """

    storage = InMemoryPhotoStorage()
    monkeypatch.setattr(jobs_module, "build_photo_storage", lambda settings: storage)

    # Aged against the **real** clock, because the job is wired with the system
    # one: a fixture instant would make this test's answer depend on the date it
    # is run on.
    orphan = PhotoRef(owner_id=ALICE, photo_id=new_uuid())
    storage.now = instant(build_clock().now() - timedelta(days=365))
    await storage.put(orphan, IMAGE, metadata={})

    settings = _nothing_but(PHOTO_SWEEP_ENABLED=True)
    (sweep,) = build_scheduled_jobs(session_factory=session_factory, settings=settings)

    with caplog.at_level(logging.INFO):
        await sweep.run_once()

    assert orphan not in storage.objects
    assert any(
        record.message == "uncommitted photo sweep finished"
        and record.photos_deleted == 1
        for record in caplog.records
    )


async def test_a_photo_inside_the_window_survives_the_wired_job(
    monkeypatch, session_factory
):
    """The other direction, through the same wiring: the retention window is a
    real input to the job and not something only the unit tests apply."""

    storage = InMemoryPhotoStorage()
    monkeypatch.setattr(jobs_module, "build_photo_storage", lambda settings: storage)

    fresh = PhotoRef(owner_id=ALICE, photo_id=new_uuid())
    storage.now = build_clock().now()
    await storage.put(fresh, IMAGE, metadata={})

    (sweep,) = build_scheduled_jobs(
        session_factory=session_factory, settings=_nothing_but(PHOTO_SWEEP_ENABLED=True)
    )
    await sweep.run_once()

    assert fresh in storage.objects


# ---------------------------------------------------------------------------
# The exposure roll
# ---------------------------------------------------------------------------


def test_the_roll_is_registered_and_carries_the_configured_cadence():
    settings = _nothing_but(
        EXPOSURE_ROLL_ENABLED=True, EXPOSURE_ROLL_INTERVAL_SECONDS=1800.0
    )

    jobs = build_scheduled_jobs(
        session_factory=None, settings=settings, redis_client=FakeRedis()
    )

    assert [job.name for job in jobs] == [EXPOSURE_ROLL_JOB]
    assert jobs[0].interval_seconds == 1800.0


def test_the_roll_without_an_ephemeral_store_refuses_to_be_registered():
    """Loudly, exactly as a database job with no session factory is.

    Unlike ``candidate_source``, a missing client is not a legitimate state: the
    lifespan opens the pool unconditionally, because the roll is one reader of
    the ledgers and every Play surface is the rest. So reaching here is a wiring
    error — and a roll that silently did not register looks precisely like a
    roll that is switched off.
    """

    settings = _nothing_but(EXPOSURE_ROLL_ENABLED=True)

    with pytest.raises(ValueError, match="redis client"):
        build_scheduled_jobs(
            session_factory=None, settings=settings, redis_client=None
        )


def test_the_roll_can_be_turned_off():
    settings = _nothing_but(EXPOSURE_ROLL_ENABLED=False)

    assert (
        build_scheduled_jobs(
            session_factory=None, settings=settings, redis_client=FakeRedis()
        )
        == []
    )


async def test_the_roll_runs_end_to_end_through_the_real_wiring():
    """The tracer: the wired job, the real ledger, and a threshold in the store.

    The client is the one thing substituted, since the real one is a network
    call. Everything else is what production runs — the fail-soft wrapper, the
    Redis adapter, the real key shapes and the real percentile.
    """

    client = FakeRedis()
    settings = _nothing_but(EXPOSURE_ROLL_ENABLED=True)
    week = week_of(build_clock().now())
    ledger = RedisExposureLedger(client)
    for times in (1, 1, 2, 11):
        await ledger.record_shown(
            sport=Sport.PADEL, week=week, player_ids=[new_uuid()] * times
        )

    (roll,) = build_scheduled_jobs(
        session_factory=None, settings=settings, redis_client=client
    )
    await roll.run_once()

    assert await client.get(busy_threshold_key(Sport.PADEL, week)) == "11"


async def test_a_roll_against_an_unreachable_store_neither_raises_nor_publishes(caplog):
    """The job inherits the ledger's posture and needs no branch of its own.

    ``run_once`` lets the failure through — that is what it is for — so a raise
    here would be a raise, not a swallowed one.
    """

    settings = _nothing_but(EXPOSURE_ROLL_ENABLED=True)

    (roll,) = build_scheduled_jobs(
        session_factory=None, settings=settings, redis_client=BrokenRedis()
    )

    with caplog.at_level(logging.INFO):
        await roll.run_once()

    assert any(
        record.message == "exposure roll finished" and record.players_counted == 0
        for record in caplog.records
        if hasattr(record, "players_counted")
    )


# ---------------------------------------------------------------------------
# The two prompt loops
# ---------------------------------------------------------------------------


def test_the_drift_loop_is_registered_and_carries_the_configured_cadence():
    """Daily, matching §14.5's own cadence — and read from the settings, so the
    number in the templates is configuration that changes something."""

    settings = _nothing_but(
        INTENT_DRIFT_ENABLED=True, INTENT_DRIFT_INTERVAL_SECONDS=3600.0
    )

    jobs = build_scheduled_jobs(
        session_factory=UNUSED_SESSIONS, settings=settings, redis_client=FakeRedis()
    )

    assert [job.name for job in jobs] == [INTENT_DRIFT_JOB]
    assert jobs[0].interval_seconds == 3600.0


def test_the_staleness_backstop_is_registered_and_carries_its_cadence():
    settings = _nothing_but(
        GRID_STALENESS_ENABLED=True, GRID_STALENESS_INTERVAL_SECONDS=7200.0
    )

    jobs = build_scheduled_jobs(
        session_factory=UNUSED_SESSIONS,
        settings=settings,
        candidate_source=object(),
        redis_client=FakeRedis(),
    )

    assert [job.name for job in jobs] == [GRID_STALENESS_JOB]
    assert jobs[0].interval_seconds == 7200.0


def test_the_backstop_is_not_registered_without_an_index_to_read():
    """A process holding no picture of the city has no grids to find stale, and
    there is nothing here to fall back to."""

    settings = _nothing_but(GRID_STALENESS_ENABLED=True)

    jobs = build_scheduled_jobs(
        session_factory=UNUSED_SESSIONS,
        settings=settings,
        candidate_source=None,
        redis_client=FakeRedis(),
    )

    assert jobs == []


def test_a_prompt_loop_without_a_store_to_leave_a_question_in_refuses():
    """Loudly, as every other job here does: *the loop is off* and *the loop was
    enabled and silently dropped* have one symptom — nobody is ever asked."""

    settings = _nothing_but(INTENT_DRIFT_ENABLED=True)

    with pytest.raises(ValueError, match="redis"):
        build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)


def test_the_drift_loop_without_a_session_factory_refuses():
    settings = _nothing_but(INTENT_DRIFT_ENABLED=True)

    with pytest.raises(ValueError, match="session factory"):
        build_scheduled_jobs(
            session_factory=None, settings=settings, redis_client=FakeRedis()
        )


async def test_the_drift_loop_runs_end_to_end_through_the_real_wiring(
    session_factory, caplog
):
    """The session, the store and the declaration repository really are assembled
    per run — and a quiet day is logged as a quiet day rather than as silence."""

    settings = _nothing_but(INTENT_DRIFT_ENABLED=True)
    (drift,) = build_scheduled_jobs(
        session_factory=session_factory, settings=settings, redis_client=FakeRedis()
    )

    with caplog.at_level(logging.INFO):
        await drift.run_once()

    assert any(
        record.message == "intent drift loop finished" and record.searches_read == 0
        for record in caplog.records
    )


# ---------------------------------------------------------------------------
# The interest expiry loop
# ---------------------------------------------------------------------------


def test_the_expiry_loop_is_registered_and_carries_the_configured_cadence():
    """Hourly by default, and read from the settings — because ``INTEREST_TTL``
    itself is emphatically **not** a setting, and only the cadence is."""

    settings = _nothing_but(
        INTEREST_EXPIRY_ENABLED=True, INTEREST_EXPIRY_INTERVAL_SECONDS=1800.0
    )

    jobs = build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)

    assert [job.name for job in jobs] == [INTEREST_EXPIRY_JOB]
    assert jobs[0].interval_seconds == 1800.0


def test_the_expiry_loop_without_a_session_factory_refuses_to_be_registered():
    """It reads the database, so it joins the loud branch rather than the quiet
    one: an expiry that silently did not register looks exactly like one that is
    off, and the symptom — a table that only grows — takes weeks to notice."""

    settings = _nothing_but(INTEREST_EXPIRY_ENABLED=True)

    with pytest.raises(ValueError, match="session factory"):
        build_scheduled_jobs(session_factory=None, settings=settings)


async def test_the_expiry_loop_runs_end_to_end_through_the_real_wiring(
    session_factory, caplog
):
    """A quiet sweep is logged as a quiet sweep, and the log line carries the
    falsifier rather than a throughput figure."""

    settings = _nothing_but(INTEREST_EXPIRY_ENABLED=True)
    (expiry,) = build_scheduled_jobs(
        session_factory=session_factory, settings=settings
    )

    with caplog.at_level(logging.INFO):
        await expiry.run_once()

    assert any(
        record.message == "interest expiry loop finished"
        and record.removed == 0
        and record.never_lifted == 0
        for record in caplog.records
    )
