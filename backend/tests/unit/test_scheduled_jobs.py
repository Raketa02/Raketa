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
from datetime import datetime, timedelta, timezone

import pytest
from uuid import UUID

import app.bootstrap.jobs as jobs_module
from app.bootstrap.composition import build_clock
from app.bootstrap.jobs import (
    CLUB_PAYOUTS_JOB,
    NEW_BOOKINGS_SUMMARY_JOB,
    CANDIDATE_INDEX_REFRESH_JOB,
    CANDIDATE_INDEX_TAIL_JOB,
    CHALLENGE_LAPSE_JOB,
    CONVERSATION_SWEEP_JOB,
    MAIL_DELIVERY_JOB,
    UNFILLED_COURT_JOB,
    RATING_CATCH_UP_JOB,
    EXPOSURE_ROLL_JOB,
    GRID_STALENESS_JOB,
    INTEREST_EXPIRY_JOB,
    INTENT_DRIFT_JOB,
    PHOTO_REVIEW_BACKFILL_JOB,
    PHOTO_SWEEP_JOB,
    PROPOSAL_EXPIRY_JOB,
    PROPOSER_JOB,
    PROPOSER_ON_CHANGES_JOB,
    SCALE_PRESSURE_JOB,
    build_scheduled_jobs,
)
from app.core.config import get_settings
from app.kernel import Sport, instant
from app.modules.matchmaking.domain.ledgers import week_of
from app.modules.matchmaking.domain.scale_triggers import (
    BYTES_PER_ROW,
    SCORING_P99_TRIGGER_MS,
    TRIGGER_WINDOW,
    footprint_of,
)
from app.modules.matchmaking.infrastructure.candidate_snapshot_source import (
    RefreshReport,
)
from app.modules.matchmaking.infrastructure.scale_instruments import ScoringMeter
from app.modules.matchmaking.infrastructure.redis_ledgers import (
    RedisExposureLedger,
    busy_threshold_key,
)
from app.modules.player_profile.domain.photos import (
    REVIEW_NOTE_METADATA_KEY,
    PhotoRef,
    PhotoReviewVerdict,
    TranscodedImage,
    verdict_from_similarities,
)
from app.shared.ids import new_uuid
from tests.unit import image_fixtures as fixtures
from tests.unit.fake_event_store import FrozenClock
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
            "PHOTO_REVIEW_BACKFILL_ENABLED": False,
            "CANDIDATE_INDEX_ENABLED": False,
            "EXPOSURE_ROLL_ENABLED": False,
            "INTENT_DRIFT_ENABLED": False,
            "GRID_STALENESS_ENABLED": False,
            "INTEREST_EXPIRY_ENABLED": False,
            "CHALLENGE_LAPSE_ENABLED": False,
            "UNFILLED_COURT_ENABLED": False,
            "RATING_CATCH_UP_ENABLED": False,
            "CONVERSATION_SWEEP_ENABLED": False,
            "MAIL_DELIVERY_ENABLED": False,
            "PROPOSAL_EXPIRY_ENABLED": False,
            "PROPOSER_ENABLED": False,
            "REQUEST_TIMEOUT_ENABLED": False,
            "CUT_OFF_ENABLED": False,
            "CLUB_PAYOUTS_ENABLED": False,
            "NEW_BOOKINGS_SUMMARY_ENABLED": False,
            "SCALE_PRESSURE_ENABLED": False,
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
# The photo re-review backfill
# ---------------------------------------------------------------------------


class _AlwaysOnCourt:
    """Stands where `ClipSidecarPhotoReview` stands, holding no policy.

    It answers similarities and lets the domain decide, because the point of the
    job is that it applies the *same* rule the upload path does — a stub verdict
    here would let a job that re-thresholded pass this tracer.
    """

    async def review(self, image: TranscodedImage) -> PhotoReviewVerdict:
        return verdict_from_similarities(
            model="test/clip", similarities=[0.9] * 5 + [0.1] * 8
        )


def test_the_backfill_is_registered_and_carries_the_configured_cadence():
    """And needs no session factory: its whole input is the object store.

    The second job here that reads no database — the exposure roll was the
    first — which is why it is registered outside the block that refuses to
    build a database job without one.
    """

    settings = _nothing_but(
        PHOTO_REVIEW_BACKFILL_ENABLED=True,
        PHOTO_REVIEW_BACKFILL_INTERVAL_SECONDS=300.0,
    )

    jobs = build_scheduled_jobs(session_factory=None, settings=settings)

    assert [job.name for job in jobs] == [PHOTO_REVIEW_BACKFILL_JOB]
    assert jobs[0].interval_seconds == 300.0


async def test_the_backfill_job_runs_end_to_end_through_the_real_wiring(
    monkeypatch, caplog
):
    """One pass-through-era photo, one run of the job's own callable, one note.

    What this proves that the use-case tests cannot: the store, the **real**
    transcoder and the reviewer are assembled from the composition root by the
    job's callable, and the budget and the pause it passes are the settings'.
    """

    storage = InMemoryPhotoStorage()
    monkeypatch.setattr(jobs_module, "build_photo_storage", lambda settings: storage)
    monkeypatch.setattr(
        jobs_module, "build_photo_review", lambda settings: _AlwaysOnCourt()
    )

    photo = PhotoRef(owner_id=ALICE, photo_id=new_uuid())
    jpeg = TranscodedImage(
        data=fixtures.plain_jpeg(), media_type="image/jpeg", width=60, height=40
    )
    # Exactly what the pass-through wrote: a decision, and nothing that says
    # anybody looked.
    await storage.put(photo, jpeg, metadata={"review": "allowed"})

    settings = _nothing_but(
        PHOTO_REVIEW_BACKFILL_ENABLED=True, PHOTO_REVIEW_BACKFILL_PAUSE_SECONDS=0.0
    )
    (backfill,) = build_scheduled_jobs(session_factory=None, settings=settings)

    with caplog.at_level(logging.INFO):
        await backfill.run_once()

    note = storage.objects[photo].metadata[REVIEW_NOTE_METADATA_KEY]
    assert note.startswith("clip;m=test/clip")
    assert any(
        record.message == "photo review backfill finished"
        and record.photos_updated == 1
        for record in caplog.records
    )


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


# ---------------------------------------------------------------------------
# The challenge lapse loop
# ---------------------------------------------------------------------------


def test_the_lapse_loop_is_registered_and_carries_the_configured_cadence():
    """The cadence is a setting; ``ANSWER_WINDOW`` is emphatically not.

    How long an invitee has to answer is the promise the invitation makes and
    lives in ``answer_window.py``; how often the loop writes down that a promise
    ran out is a fact about the deployment.
    """

    settings = _nothing_but(
        CHALLENGE_LAPSE_ENABLED=True, CHALLENGE_LAPSE_INTERVAL_SECONDS=900.0
    )

    jobs = build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)

    assert [job.name for job in jobs] == [CHALLENGE_LAPSE_JOB]
    assert jobs[0].interval_seconds == 900.0


def test_the_lapse_loop_without_a_session_factory_refuses_to_be_registered():
    """It reads the log, so it joins the loud branch: a loop that silently did
    not register looks exactly like one that is off, and its symptom — a Strand
    with no denominator — is invisible until somebody asks for the number."""

    settings = _nothing_but(CHALLENGE_LAPSE_ENABLED=True)

    with pytest.raises(ValueError, match="session factory"):
        build_scheduled_jobs(session_factory=None, settings=settings)


async def test_the_lapse_loop_runs_end_to_end_through_the_real_wiring(
    session_factory, caplog
):
    """A quiet sweep is logged as a quiet sweep, and the line carries the three
    figures the record exists for rather than a duration."""

    settings = _nothing_but(CHALLENGE_LAPSE_ENABLED=True)
    (lapse,) = build_scheduled_jobs(session_factory=session_factory, settings=settings)

    with caplog.at_level(logging.INFO):
        await lapse.run_once()

    assert any(
        record.message == "challenge lapse loop finished"
        and record.seats == 0
        and record.challenges == 0
        and record.conflicts == 0
        for record in caplog.records
    )


# ---------------------------------------------------------------------------
# The hour loop (docs/adr/0175 §3)
# ---------------------------------------------------------------------------


def test_the_hour_loop_is_registered_and_carries_the_configured_cadence():
    """A minute, because the interval is how long a court past its hour reads
    *needs a player* with nothing to press — a fact about the deployment and
    not about any court."""

    settings = _nothing_but(
        UNFILLED_COURT_ENABLED=True, UNFILLED_COURT_INTERVAL_SECONDS=30.0
    )

    jobs = build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)

    assert [job.name for job in jobs] == [UNFILLED_COURT_JOB]
    assert jobs[0].interval_seconds == 30.0


def test_the_hour_loop_without_a_session_factory_refuses_to_be_registered():
    """It reads the log and correctness depends on it, so it joins the loud
    branch twice over: a loop that silently did not register would leave
    every unfilled court reading *needs a player* for ever."""

    settings = _nothing_but(UNFILLED_COURT_ENABLED=True)

    with pytest.raises(ValueError, match="session factory"):
        build_scheduled_jobs(session_factory=None, settings=settings)


async def test_the_hour_loop_runs_end_to_end_through_the_real_wiring(
    session_factory, caplog
):
    """A quiet sweep is logged as a quiet sweep, with the two figures the
    record exists for."""

    settings = _nothing_but(UNFILLED_COURT_ENABLED=True)
    (hour,) = build_scheduled_jobs(session_factory=session_factory, settings=settings)

    with caplog.at_level(logging.INFO):
        await hour.run_once()

    assert any(
        record.message == "unfilled court loop finished"
        and record.courts == 0
        and record.conflicts == 0
        for record in caplog.records
    )


# ---------------------------------------------------------------------------
# The two trigger instruments (scale-posture.md §4)
#
# What is asserted is that the record is emitted and carries the fields the
# trigger is stated in. **No wall-clock, no p99 and no rate of this machine's
# own** — those are metrics, and a metric asserted on a shared runner is a mute
# waiting to happen.
# ---------------------------------------------------------------------------


def test_the_pressure_probe_is_registered_and_carries_the_configured_cadence():
    """It needs no session, no store and no index — it reads this process's own
    counters, which is why it is the one job a process with everything else
    switched off still runs."""

    settings = _nothing_but(SCALE_PRESSURE_ENABLED=True)
    meter = ScoringMeter()

    jobs = build_scheduled_jobs(
        session_factory=None, settings=settings, meter=meter
    )

    assert [job.name for job in jobs] == [SCALE_PRESSURE_JOB]
    assert jobs[0].interval_seconds == settings.SCALE_PRESSURE_INTERVAL_SECONDS


def test_the_probe_is_not_registered_without_a_histogram_to_read():
    """A process that scores nothing has no window to close, and there is
    nothing here to fall back to."""

    settings = _nothing_but(SCALE_PRESSURE_ENABLED=True)

    assert build_scheduled_jobs(session_factory=None, settings=settings) == []


async def test_a_window_that_closes_writes_one_record_naming_both_halves(caplog):
    """One record per window, and it says which half of trigger 1 fired.

    The window is closed by advancing the probe's own duration source rather
    than by waiting fifteen minutes, so what this asserts is the record's shape
    and the arithmetic behind it — never a timing this runner produced.
    """

    settings = _nothing_but(SCALE_PRESSURE_ENABLED=True)
    elapsed = [0.0]
    meter = ScoringMeter(monotonic=lambda: elapsed[0])
    # The meter the job's probe reads is this one, so *fifteen minutes have
    # passed* is one statement rather than two that could disagree.
    job = jobs_module.build_scale_pressure_job(meter=meter, settings=settings)

    meter.observe_scoring(2.0)
    with caplog.at_level(logging.INFO, logger="app.bootstrap.jobs"):
        await job.run_once()
        assert not [r for r in caplog.records if r.msg == "scoring pressure window"]
        elapsed[0] += TRIGGER_WINDOW.total_seconds()
        await job.run_once()

    written = [r for r in caplog.records if r.msg == "scoring pressure window"]
    assert len(written) == 1
    record = written[0]
    assert record.levelno == logging.INFO
    assert record.job == SCALE_PRESSURE_JOB
    assert record.scoring_calls == 1
    assert record.trigger_1_fires is False
    assert record.trigger_1_p99_crossed is False
    assert record.trigger_1_duty_cycle_crossed is False
    assert hasattr(record, "loop_lag_p99_ms")


async def test_a_window_that_fires_the_trigger_leaves_the_healthy_level(caplog):
    """A boolean field on an INFO line is a thing nobody is paged by, which is
    the same as not raising one."""

    settings = _nothing_but(SCALE_PRESSURE_ENABLED=True)
    elapsed = [0.0]
    meter = ScoringMeter(monotonic=lambda: elapsed[0])
    job = jobs_module.build_scale_pressure_job(meter=meter, settings=settings)

    for _ in range(100):
        meter.observe_scoring(SCORING_P99_TRIGGER_MS + 1.0)
    with caplog.at_level(logging.INFO, logger="app.bootstrap.jobs"):
        await job.run_once()
        elapsed[0] += TRIGGER_WINDOW.total_seconds()
        await job.run_once()

    record = [r for r in caplog.records if r.msg == "scoring pressure window"][0]
    assert record.levelno == logging.WARNING
    assert record.trigger_1_fires is True
    assert record.trigger_1_p99_crossed is True


async def test_the_refresh_record_carries_trigger_fours_arithmetic(caplog):
    """*Recomputed at every index load*, from the rows this worker holds, the
    workers configured and the container's own limit — and it rides on the
    refresh's own record, because a second line would have to say which load it
    was about."""

    settings = _nothing_but(CANDIDATE_INDEX_ENABLED=True, GUNICORN_WORKERS=4)
    now = instant(datetime(2026, 8, 26, 18, 0, tzinfo=timezone.utc))

    class OneRow:
        async def refresh(self):
            return RefreshReport(
                snapshot_version=7,
                partitions=1,
                rows_held=1_000,
                rows_decoded=1,
                caught_up_at=now,
            )

    # **A gigabyte, stated by the test and not read off the runner.** The
    # container this asserts about has to be one this suite chose: a CI machine
    # has whatever cgroup it has, and an assertion about its memory is an
    # assertion about the runner.
    job = jobs_module.build_candidate_index_refresh_job(
        source=OneRow(),
        settings=settings,
        clock=FrozenClock(now),
        memory_limit_bytes=1_000_000_000,
    )
    with caplog.at_level(logging.INFO, logger="app.bootstrap.jobs"):
        await job.run_once()

    record = [r for r in caplog.records if r.msg == "candidate index refreshed"][0]
    assert record.levelno == logging.INFO
    assert record.workers == 4
    assert record.container_memory_limit_bytes == 1_000_000_000
    assert record.index_bytes_held == BYTES_PER_ROW * 1_000 * 4
    # §4's own stated bound, reached through the job rather than restated —
    # and moved with `BYTES_PER_ROW`, which is the whole point of reaching it.
    assert record.trigger_4_players_at == 24_801
    assert record.trigger_4_fires is False


async def test_an_index_over_half_its_container_warns_and_still_refreshes(caplog):
    """**Warning and never refusing.** An index that has outgrown half the
    container is a capacity decision — `array`-packed columns at 43 bytes a row
    — and a process that refused to load it would take the platform down to
    avoid using memory it had been given."""

    settings = _nothing_but(CANDIDATE_INDEX_ENABLED=True, GUNICORN_WORKERS=4)
    now = instant(datetime(2026, 8, 26, 18, 0, tzinfo=timezone.utc))

    class ACityTooBig:
        async def refresh(self):
            return RefreshReport(
                snapshot_version=7,
                partitions=1,
                rows_held=200_000,
                rows_decoded=1,
                caught_up_at=now,
            )

    job = jobs_module.build_candidate_index_refresh_job(
        source=ACityTooBig(),
        settings=settings,
        clock=FrozenClock(now),
        memory_limit_bytes=1_000_000_000,
    )
    with caplog.at_level(logging.INFO, logger="app.bootstrap.jobs"):
        await job.run_once()

    record = [r for r in caplog.records if r.msg == "candidate index refreshed"][0]
    assert record.trigger_4_fires is True
    assert record.levelno == logging.WARNING
    # The refresh itself is untouched: the index was published either way.
    assert record.snapshot_version == 7


def test_a_host_with_no_container_limit_reports_unknown_rather_than_roomy() -> None:
    """Trigger 4 cannot fire where there is no limit to be half of, and
    **unknown is not unlimited** — which is a laptop, and every run of this
    suite."""

    footprint = footprint_of(rows=10_000_000, workers=4, limit_bytes=None)
    assert footprint.fraction_of_budget is None
    assert not footprint.fires


# ---------------------------------------------------------------------------
# The rating catch-up — the only loop here that correctness depends on
# ---------------------------------------------------------------------------


def test_the_catch_up_is_registered_and_carries_the_configured_cadence():
    """The cadence is a setting; **the update rule is emphatically not.**

    How often a confirmed result reaches a Level is a fact about the deployment.
    What it does to that Level is `engines/racketskill/results.py`, and an
    environment that could pick a K-factor is an environment that decides how a
    marketplace rates people (``docs/adr/0139``).
    """

    settings = _nothing_but(
        RATING_CATCH_UP_ENABLED=True, RATING_CATCH_UP_INTERVAL_SECONDS=900.0
    )

    jobs = build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)

    assert [job.name for job in jobs] == [RATING_CATCH_UP_JOB]
    assert jobs[0].interval_seconds == 900.0


def test_the_catch_up_without_a_session_factory_refuses_to_be_registered():
    """It reads the log and writes streams, so it joins the loud branch.

    And its symptom is worse than the others': a loop that silently did not
    register looks exactly like one that is off, and what stops is **every Level
    on the platform being tested** — which nothing complains about, because a
    rating that has not moved looks exactly like a rating nobody has played.
    """

    settings = _nothing_but(RATING_CATCH_UP_ENABLED=True)

    with pytest.raises(ValueError, match="session factory"):
        build_scheduled_jobs(session_factory=None, settings=settings)


async def test_the_catch_up_runs_end_to_end_through_the_real_wiring(
    session_factory, caplog
):
    """A quiet run is logged as a quiet run, with the four figures it exists for.

    ``unrated_seats`` is on that line rather than swallowed because *nobody
    played* and *everybody who played was unrated in that sport* both show up as
    nothing moving, and only one of them is a defect.
    """

    settings = _nothing_but(RATING_CATCH_UP_ENABLED=True)
    (catch_up,) = build_scheduled_jobs(
        session_factory=session_factory, settings=settings
    )

    with caplog.at_level(logging.INFO):
        await catch_up.run_once()

    assert any(
        record.message == "rating catch-up finished"
        and record.games == 0
        and record.ratings == 0
        and record.unrated_seats == 0
        and record.conflicts == 0
        for record in caplog.records
    )


def test_the_conversation_sweep_is_registered_and_carries_the_configured_cadence():
    """The cadence is a setting; **``CONVERSATION_GRACE`` is emphatically not.**

    How often dead rooms are cleared out is a fact about the deployment. How long
    a room outlives the game it was opened for is behaviour a domain test can
    observe, and it lives in `conversations/domain/lifetime.py` (``docs/adr/0153``
    §4).
    """

    settings = _nothing_but(
        CONVERSATION_SWEEP_ENABLED=True, CONVERSATION_SWEEP_INTERVAL_SECONDS=900.0
    )

    jobs = build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)

    assert [job.name for job in jobs] == [CONVERSATION_SWEEP_JOB]
    assert jobs[0].interval_seconds == 900.0


def test_the_conversation_sweep_without_a_session_factory_refuses_to_be_registered():
    """It walks the conversation table and deletes streams, so it joins the loud
    branch: *the sweep is off* and *the sweep was enabled and silently dropped*
    have one symptom — rooms accumulating — and only one is somebody's decision.
    """

    settings = _nothing_but(CONVERSATION_SWEEP_ENABLED=True)

    with pytest.raises(ValueError, match="session factory"):
        build_scheduled_jobs(session_factory=None, settings=settings)


async def test_the_conversation_sweep_runs_end_to_end_through_the_real_wiring(
    session_factory, caplog
):
    """A quiet run is logged as a quiet run, with both figures it exists for.

    ``rooms`` is on that line beside ``destroyed`` because *the loop is off* and
    *the loop is running and nothing has ended* both show up as rooms
    accumulating, and only one of them is somebody's problem.
    """

    settings = _nothing_but(CONVERSATION_SWEEP_ENABLED=True)
    (sweep,) = build_scheduled_jobs(
        session_factory=session_factory, settings=settings
    )

    with caplog.at_level(logging.INFO):
        await sweep.run_once()

    assert any(
        record.message == "conversation sweep finished"
        and record.rooms == 0
        and record.destroyed == 0
        for record in caplog.records
    )


def test_the_mail_worker_is_registered_and_carries_the_configured_cadence():
    """How often the queue is drained is a setting; what is sent, and how long
    the link in it works, are not (``docs/adr/0186``)."""

    settings = _nothing_but(
        MAIL_DELIVERY_ENABLED=True, MAIL_DELIVERY_INTERVAL_SECONDS=5.0
    )

    jobs = build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)

    assert [job.name for job in jobs] == [MAIL_DELIVERY_JOB]
    assert jobs[0].interval_seconds == 5.0


def test_the_mail_worker_without_a_session_factory_refuses_to_be_registered():
    """A worker enabled and silently dropped is a table of live secrets nobody
    receives, which looks exactly like a quiet day."""

    settings = _nothing_but(MAIL_DELIVERY_ENABLED=True)

    with pytest.raises(ValueError, match="session factory"):
        build_scheduled_jobs(session_factory=None, settings=settings)


async def test_the_mail_worker_sends_through_the_configured_mailer(
    monkeypatch, session_factory, caplog
):
    """One queued message, one run of the job's own callable, one send — and a
    log line that says so."""

    from app.application.ports.mail import OutgoingMessage
    from app.bootstrap.composition import build_mail_queue
    from tests.unit.fake_mailer import RecordingMailer

    mailer = RecordingMailer()
    monkeypatch.setattr(jobs_module, "build_mailer", lambda settings: mailer)
    message = OutgoingMessage(
        kind="forgot_password.player",
        to="tomek@example.com",
        subject="Set a new Raketa password",
        text="text",
        html="<p>html</p>",
    )
    async with session_factory() as session:
        await build_mail_queue(session).enqueue(message, at=build_clock().now())
        await session.commit()
    (worker,) = build_scheduled_jobs(
        session_factory=session_factory,
        settings=_nothing_but(MAIL_DELIVERY_ENABLED=True),
    )

    with caplog.at_level(logging.INFO):
        await worker.run_once()

    assert mailer.sent == [message]
    assert any(
        record.message == "mail delivery run finished" and record.sent == 1
        for record in caplog.records
    )


def test_the_book_by_sweep_is_registered_and_carries_the_configured_cadence():
    """How often an expiry is recorded is a setting; when a proposal expires is
    the club's book-by, and never configuration."""

    settings = _nothing_but(
        PROPOSAL_EXPIRY_ENABLED=True, PROPOSAL_EXPIRY_INTERVAL_SECONDS=30.0
    )

    jobs = build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)

    assert [job.name for job in jobs] == [PROPOSAL_EXPIRY_JOB]
    assert jobs[0].interval_seconds == 30.0


def test_the_book_by_sweep_without_a_session_factory_refuses_to_be_registered():
    settings = _nothing_but(PROPOSAL_EXPIRY_ENABLED=True)

    with pytest.raises(ValueError, match="session factory"):
        build_scheduled_jobs(session_factory=None, settings=settings)


async def test_the_book_by_sweep_runs_end_to_end_through_the_real_wiring(
    session_factory, caplog
):
    """A sweep with nothing past its book-by writes nothing and says nothing."""

    (sweep,) = build_scheduled_jobs(
        session_factory=session_factory,
        settings=_nothing_but(PROPOSAL_EXPIRY_ENABLED=True),
    )

    with caplog.at_level(logging.INFO):
        await sweep.run_once()

    assert not any(
        record.message == "proposal expiry finished" for record in caplog.records
    )


def test_the_proposer_is_registered_with_its_short_tick_and_their_cadences():
    """How often the proposer looks is a setting; what it deals is domain
    (``proposals/domain/proposer.py``). The short tick needs what the process's
    delivery tells it, so it is registered only where there is one."""

    from app.modules.proposals.application.propose_games import DueForProposing

    settings = _nothing_but(
        PROPOSER_ENABLED=True,
        PROPOSER_INTERVAL_SECONDS=120.0,
        PROPOSER_ON_CHANGES_INTERVAL_SECONDS=3.0,
    )

    told = build_scheduled_jobs(
        session_factory=UNUSED_SESSIONS,
        settings=settings,
        proposer_due=DueForProposing(),
    )
    untold = build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)

    assert [(job.name, job.interval_seconds) for job in told] == [
        (PROPOSER_JOB, 120.0),
        (PROPOSER_ON_CHANGES_JOB, 3.0),
    ]
    assert [job.name for job in untold] == [PROPOSER_JOB]


def test_the_proposer_without_a_session_factory_refuses_to_be_registered():
    with pytest.raises(ValueError, match="session factory"):
        build_scheduled_jobs(
            session_factory=None, settings=_nothing_but(PROPOSER_ENABLED=True)
        )


async def test_the_proposer_runs_end_to_end_through_the_real_wiring(
    session_factory, caplog
):
    """A sweep over no pools deals nothing and says nothing; a tick with
    nothing due does not open a session at all."""

    from app.modules.proposals.application.propose_games import DueForProposing

    sweep, tick = build_scheduled_jobs(
        session_factory=session_factory,
        settings=_nothing_but(PROPOSER_ENABLED=True),
        proposer_due=DueForProposing(),
    )
    (idle,) = [
        job
        for job in build_scheduled_jobs(
            session_factory=UNUSED_SESSIONS,
            settings=_nothing_but(PROPOSER_ENABLED=True),
            proposer_due=DueForProposing(),
        )
        if job.name == PROPOSER_ON_CHANGES_JOB
    ]

    with caplog.at_level(logging.INFO):
        await sweep.run_once()
        await tick.run_once()
        await idle.run_once()

    assert not any(record.message == "proposer finished" for record in caplog.records)


def test_the_payouts_and_the_new_bookings_summary_are_registered_with_their_cadences():
    """How often a club's closed day is looked at is a setting; that a club is
    paid after its games are played, and told its day once it closes, is
    domain (#548)."""

    settings = _nothing_but(
        CLUB_PAYOUTS_ENABLED=True,
        CLUB_PAYOUTS_INTERVAL_SECONDS=300.0,
        NEW_BOOKINGS_SUMMARY_ENABLED=True,
        NEW_BOOKINGS_SUMMARY_INTERVAL_SECONDS=600.0,
    )

    jobs = build_scheduled_jobs(session_factory=UNUSED_SESSIONS, settings=settings)

    assert [(job.name, job.interval_seconds) for job in jobs] == [
        (CLUB_PAYOUTS_JOB, 300.0),
        (NEW_BOOKINGS_SUMMARY_JOB, 600.0),
    ]


def test_the_payouts_and_the_summary_without_a_session_factory_refuse():
    for flag in ("CLUB_PAYOUTS_ENABLED", "NEW_BOOKINGS_SUMMARY_ENABLED"):
        with pytest.raises(ValueError, match="session factory"):
            build_scheduled_jobs(
                session_factory=None, settings=_nothing_but(**{flag: True})
            )


async def test_the_payouts_and_the_summary_run_end_to_end_through_the_real_wiring(
    session_factory, caplog
):
    """With nothing owed and nothing booked, both runs write nothing and say
    nothing."""

    payouts, summary = build_scheduled_jobs(
        session_factory=session_factory,
        settings=_nothing_but(
            CLUB_PAYOUTS_ENABLED=True, NEW_BOOKINGS_SUMMARY_ENABLED=True
        ),
    )

    with caplog.at_level(logging.INFO):
        await payouts.run_once()
        await summary.run_once()

    assert not any(
        record.message in ("club payouts finished", "new bookings summary finished")
        for record in caplog.records
    )
