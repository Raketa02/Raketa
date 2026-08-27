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
from uuid import UUID

import app.bootstrap.jobs as jobs_module
from app.bootstrap.composition import build_clock
from app.bootstrap.jobs import (
    CANDIDATE_INDEX_REFRESH_JOB,
    CANDIDATE_INDEX_TAIL_JOB,
    PHOTO_SWEEP_JOB,
    build_scheduled_jobs,
)
from app.core.config import get_settings
from app.kernel import instant
from app.modules.player_profile.domain.photos import PhotoRef, TranscodedImage
from app.shared.ids import new_uuid
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

ALICE = UUID("11111111-1111-1111-1111-111111111111")
IMAGE = TranscodedImage(data=b"jpeg", media_type="image/jpeg", width=10, height=10)


def test_the_sweep_is_registered_and_carries_the_configured_cadence():
    """The cadence is read from the settings and not hard-coded in the job.

    Asserted rather than assumed, because the alternative — a constant in
    `jobs.py` — would leave `PHOTO_SWEEP_INTERVAL_SECONDS` in the templates and
    the README as configuration that changes nothing.
    """

    settings = _only_the_sweep(PHOTO_SWEEP_INTERVAL_SECONDS=900.0)

    jobs = build_scheduled_jobs(session_factory=None, settings=settings)

    assert [job.name for job in jobs] == [PHOTO_SWEEP_JOB]
    assert jobs[0].interval_seconds == 900.0


def test_a_job_that_is_turned_off_is_not_registered():
    """Off is off — not built and then never started, which would still hold
    whatever its construction reached for."""

    settings = get_settings().model_copy(
        update={"PHOTO_SWEEP_ENABLED": False, "CANDIDATE_INDEX_ENABLED": False}
    )

    assert build_scheduled_jobs(session_factory=None, settings=settings) == []


def test_the_candidate_index_registers_two_loops_and_not_one():
    """The tail writes the shared tables; the refresh rebuilds this worker's own.

    Two jobs rather than one with two phases, because they are safe beside
    themselves for opposite reasons: the tail because a single cursor row taken
    ``FOR UPDATE`` serialises it, the refresh because being **per worker** is the
    behaviour wanted rather than the cost paid (``docs/adr/0092``,
    ``docs/adr/0112``).
    """

    settings = get_settings().model_copy(update={"PHOTO_SWEEP_ENABLED": False})
    source = object()

    jobs = build_scheduled_jobs(
        session_factory=None, settings=settings, candidate_source=source
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

    settings = get_settings().model_copy(update={"PHOTO_SWEEP_ENABLED": False})

    jobs = build_scheduled_jobs(
        session_factory=None, settings=settings, candidate_source=None
    )

    assert [job.name for job in jobs] == [CANDIDATE_INDEX_TAIL_JOB]


def _only_the_sweep(**overrides):
    return get_settings().model_copy(
        update={"CANDIDATE_INDEX_ENABLED": False, **overrides}
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

    settings = _only_the_sweep()
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
        session_factory=session_factory, settings=_only_the_sweep()
    )
    await sweep.run_once()

    assert fresh in storage.objects
