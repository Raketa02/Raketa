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
    CLUB_PAYOUTS_JOB,
    NEW_BOOKINGS_SUMMARY_JOB,
    CONVERSATION_SWEEP_JOB,
    MAIL_DELIVERY_JOB,
    RATING_CATCH_UP_JOB,
    PHOTO_REVIEW_BACKFILL_JOB,
    PHOTO_SWEEP_JOB,
    PROPOSAL_EXPIRY_JOB,
    PROPOSER_JOB,
    PROPOSER_ON_CHANGES_JOB,
    build_scheduled_jobs,
)
from app.core.config import get_settings
from app.kernel import instant
from app.modules.player_profile.domain.photos import (
    REVIEW_NOTE_METADATA_KEY,
    PhotoRef,
    PhotoReviewVerdict,
    TranscodedImage,
    verdict_from_similarities,
)
from app.shared.ids import new_uuid
from tests.unit import image_fixtures as fixtures
from tests.unit.fake_photo_storage import InMemoryPhotoStorage

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


def test_a_database_job_without_a_session_factory_refuses_to_be_registered():
    """Loudly, rather than by registering nothing.

    *The sweep is off* and *the sweep was enabled and silently dropped* have one
    symptom — orphans accumulating — and only one of them is somebody's
    decision. The parameter is optional because the photo re-review backfill
    wants no session, which is exactly where that hole could open.
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
            "RATING_CATCH_UP_ENABLED": False,
            "CONVERSATION_SWEEP_ENABLED": False,
            "MAIL_DELIVERY_ENABLED": False,
            "PROPOSAL_EXPIRY_ENABLED": False,
            "PROPOSER_ENABLED": False,
            "REQUEST_TIMEOUT_ENABLED": False,
            "TIME_TO_PAY_ENABLED": False,
            "CUT_OFF_ENABLED": False,
            "CLUB_PAYOUTS_ENABLED": False,
            "NEW_BOOKINGS_SUMMARY_ENABLED": False,
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
