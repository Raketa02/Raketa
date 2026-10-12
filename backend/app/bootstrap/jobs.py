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
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_ask_how_did_it_go,
    build_propose_games,
    build_clock,
    build_destroy_ended_conversations,
    build_domain_event_store,
    build_event_publisher,
    build_expire_proposals,
    build_expire_unanswered_requests,
    build_payment_provider,
    build_run_out_the_time_to_pay,
    build_the_cut_off,
    build_the_holding,
    build_decide_club_payouts,
    build_image_transcoder,
    build_mailer,
    build_pending_mail,
    build_photo_review,
    build_photo_storage,
    build_player_profile_repository,
    build_settle_ratings_on_results,
    build_summarise_new_bookings,
    build_unit_of_work,
)
from app.application.mail.deliver_queued_mail import DeliverQueuedMail
from app.core.config import Settings
from app.infrastructure.jobs import PeriodicJob
from app.modules.player_profile.application.review_unreviewed_photos import (
    ReviewUnreviewedPhotos,
)
from app.modules.player_profile.application.sweep_uncommitted_photos import (
    SweepUncommittedPhotos,
)
from app.modules.proposals.application.propose_games import (
    DueForProposing,
    ProposeGames,
    Proposed,
)

logger = logging.getLogger(__name__)

#: The sweep's name in the logs and on its asyncio task.
PHOTO_SWEEP_JOB = "uncommitted-photo-sweep"

#: The re-review backfill's name. It walks the **same bucket** the sweep does
#: and the two have no lock between them, which is a race each of them handles
#: rather than one they coordinate over (``docs/adr/0132``).
PHOTO_REVIEW_BACKFILL_JOB = "photo-review-backfill"

#: The rating catch-up. The **first** job that writes a domain event, and the
#: only one on this list whose output a player would miss: a result a window
#: closing settled is a clock passing and announces nothing (``docs/adr/0137``),
#: so without this it never reaches a Level — every minute, so Levels move within
#: one of it (``docs/adr/0195`` §5). An agreement settles at once and moves its
#: Levels from the outbox (#654). It holds no cursor — the rating streams are the
#: cursor (``docs/adr/0139``) — so *N processes, N runs* costs a repeated read
#: and a counted collision, and a run that dies half way is re-derived in full by
#: the next tick.
RATING_CATCH_UP_JOB = "rating-catch-up"

#: The conversation sweep. The one job here that deletes an aggregate:
#: *destroyed, not delisted* (``docs/adr/0142``, with its instant moved by
#: ``docs/adr/0153``). It buys a store the size of what is live and nothing a
#: player can see — every route already answers ``conversation_not_found`` past
#: a room's end.
CONVERSATION_SWEEP_JOB = "conversation-sweep"

#: The book-by sweep (#538). It appends a ``ProposalExpired`` to every proposal
#: whose book-by passed unfilled — **the record, not the fact**: a proposal is
#: over from its book-by on whether or not this has run, so nobody is told and
#: nothing a player reads waits on it.
PROPOSAL_EXPIRY_JOB = "proposal-expiry"

#: The On request timeout (#543). It calls off every request an On request club
#: did not answer in its time to confirm — and **correctness depends on it**:
#: every read refuses an answer past the deadline already, but only this frees
#: the court the request held and makes its players due a new card first.
REQUEST_TIMEOUT_JOB = "request-timeout"

#: Time to pay (#625, #626). It runs out every refused share's time to pay that
#: is up — the seat reopens for everybody, the holds kept for it are let go, and
#: at the club's yes the booking is called off and its court freed — and
#: **correctness depends on it**: a payer's own act past the time already runs
#: it out first, but nothing else does it for the others.
TIME_TO_PAY_JOB = "time-to-pay"

#: The cut-off (#544). It calls off every booked game whose cut-off came with
#: a seat open since before it — **a game plays full or not at all** — and
#: **correctness depends on it**: every read says *called off* from the cut-off
#: on already, but only this gives everybody still in their money back, frees
#: the court and emails the club.
CUT_OFF_JOB = "cut-off"

#: The holding (#639). Four days before each booked game's cut-off it holds
#: every share the fill only checked — its card's hold would not have lasted
#: until the cut-off — and gives a refused one's player their time to fix the
#: card. **Correctness depends on it**: until it runs, a checked share is held
#: nowhere, and the cut-off has nothing of that player's to take.
HOLDING_JOB = "holding"

#: How did it go? (#663). When a Competitive booked game's hour ends, all four
#: are asked for the score while they are still at the club. A clock passing
#: announces nothing, so nothing else asks: the result screen and Home still
#: wait for a score whether or not this has run.
HOW_DID_IT_GO_JOB = "how-did-it-go"

#: Club payouts (#548). At the close of every club day it decides, per club, one
#: payout of what its games over by then left it — played, or called off with
#: what that gives back decided; the outbox makes it and tells the desk.
#: **Correctness depends on it**: nothing else pays a club.
CLUB_PAYOUTS_JOB = "club-payouts"

#: The club's daily summary of new bookings (#548): once a club day closes, its
#: desk is emailed every game booked that day. The record, not the fact — the
#: Bookings page shows a booking the moment it is made.
NEW_BOOKINGS_SUMMARY_JOB = "new-bookings-summary"

#: The proposer (#540) — **the engine that builds games**, and the second job
#: on this list correctness depends on: nothing else deals a pick, re-deals a
#: seat a no left or widens a pick at half In. It writes through the dealer's
#: own acts, one transaction each, and a pick's id is its game, so N processes
#: running it at once make each game once and count the rest as refused.
PROPOSER_JOB = "proposer"
#: Its short tick: the pools a change this process delivered made due. **Best
#: effort** — a restart forgets what was due, and the sweep above sees it.
PROPOSER_ON_CHANGES_JOB = "proposer-on-changes"

#: The mail worker (``docs/adr/0186`` §2). A queue drain written as a job, like
#: the outbox: it sends what a use case left in the mail queue and purges the
#: body — **the purge is the control** on a live secret sitting in the database,
#: so turning this off is a table of links and codes nobody receives.
MAIL_DELIVERY_JOB = "mail-delivery"


def build_scheduled_jobs(
    *,
    session_factory: async_sessionmaker[AsyncSession] | None,
    settings: Settings,
    proposer_due: DueForProposing | None = None,
) -> list[PeriodicJob]:
    """Every job this process should run, in the order they were registered.

    A list rather than a single object, so adding the next one is appending a
    line here and changing nothing in the lifespan that starts them.

    ``session_factory`` is optional because **the photo re-review backfill wants
    none** — its whole input and output are the object store. It is still
    required by every job that reads the database, and omitting it while one of
    those is enabled raises rather than quietly registering nothing.
    """

    jobs: list[PeriodicJob] = []
    if (
        settings.PHOTO_SWEEP_ENABLED
        or settings.RATING_CATCH_UP_ENABLED
        or settings.CONVERSATION_SWEEP_ENABLED
        or settings.MAIL_DELIVERY_ENABLED
        or settings.PROPOSAL_EXPIRY_ENABLED
        or settings.PROPOSER_ENABLED
        or settings.REQUEST_TIMEOUT_ENABLED
        or settings.TIME_TO_PAY_ENABLED
        or settings.CUT_OFF_ENABLED
        or settings.HOLDING_ENABLED
        or settings.HOW_DID_IT_GO_ENABLED
        or settings.CLUB_PAYOUTS_ENABLED
        or settings.NEW_BOOKINGS_SUMMARY_ENABLED
    ):
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
        if settings.RATING_CATCH_UP_ENABLED:
            jobs.append(
                build_rating_catch_up_job(
                    session_factory=session_factory, settings=settings
                )
            )
        if settings.CONVERSATION_SWEEP_ENABLED:
            jobs.append(
                build_conversation_sweep_job(
                    session_factory=session_factory, settings=settings
                )
            )
        if settings.MAIL_DELIVERY_ENABLED:
            jobs.append(
                build_mail_delivery_job(
                    session_factory=session_factory, settings=settings
                )
            )
        if settings.PROPOSAL_EXPIRY_ENABLED:
            jobs.append(
                build_proposal_expiry_job(
                    session_factory=session_factory, settings=settings
                )
            )
        if settings.REQUEST_TIMEOUT_ENABLED:
            jobs.append(
                build_request_timeout_job(
                    session_factory=session_factory, settings=settings
                )
            )
        if settings.TIME_TO_PAY_ENABLED:
            jobs.append(
                build_time_to_pay_job(
                    session_factory=session_factory, settings=settings
                )
            )
        if settings.CUT_OFF_ENABLED:
            jobs.append(
                build_cut_off_job(session_factory=session_factory, settings=settings)
            )
        if settings.HOLDING_ENABLED:
            jobs.append(
                build_holding_job(session_factory=session_factory, settings=settings)
            )
        if settings.HOW_DID_IT_GO_ENABLED:
            jobs.append(
                build_how_did_it_go_job(
                    session_factory=session_factory, settings=settings
                )
            )
        if settings.CLUB_PAYOUTS_ENABLED:
            jobs.append(
                build_club_payouts_job(
                    session_factory=session_factory, settings=settings
                )
            )
        if settings.NEW_BOOKINGS_SUMMARY_ENABLED:
            jobs.append(
                build_new_bookings_summary_job(
                    session_factory=session_factory, settings=settings
                )
            )
        if settings.PROPOSER_ENABLED:
            jobs.append(
                build_proposer_job(session_factory=session_factory, settings=settings)
            )
            # The short tick only where a delivery tells it something: with no
            # outbox drain in this process, nothing would ever be due.
            if proposer_due is not None:
                jobs.append(
                    build_proposer_on_changes_job(
                        session_factory=session_factory,
                        settings=settings,
                        due=proposer_due,
                    )
                )
    if settings.PHOTO_REVIEW_BACKFILL_ENABLED:
        # Outside the block above, because this is the second job here that
        # reads no database at all: its whole input is the object store and its
        # whole output is metadata on the objects it read. Nothing to guard, so
        # nothing to raise about.
        jobs.append(build_photo_review_backfill(settings=settings))
    return jobs


def build_mail_delivery_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Send what is due in the mail queue, one message per transaction.

    **Safe beside itself with no lock** (``docs/adr/0092``) because each message
    is claimed ``FOR UPDATE SKIP LOCKED`` for exactly its own send: a second
    process skips it rather than waiting for it or taking it too. What *N
    processes* cannot rule out is a process dying between a send and its commit,
    which sends that message again — at least once, and a duplicate reset email
    carries the same link and code as the first (``docs/adr/0186`` §2).

    **Correctness depends on it**, in the way the rating catch-up's does: nobody
    receives a reset or an invitation until this runs, and a secret sits in the
    table until this purges it. The mailer is built once, because it holds no
    connection between sends.
    """

    clock = build_clock()
    mailer = build_mailer(settings)

    async def run() -> None:
        async with session_factory() as session:
            outcome = await DeliverQueuedMail(
                pending=build_pending_mail(session),
                mailer=mailer,
                uow=build_unit_of_work(session),
                clock=clock,
                batch_size=settings.MAIL_DELIVERY_BATCH_SIZE,
            ).execute()
        if outcome.sent or outcome.failed:
            logger.log(
                logging.WARNING if outcome.given_up else logging.INFO,
                "mail delivery run finished",
                extra={
                    "job": MAIL_DELIVERY_JOB,
                    "sent": outcome.sent,
                    "failed": outcome.failed,
                    "given_up": outcome.given_up,
                },
            )

    return PeriodicJob(
        name=MAIL_DELIVERY_JOB,
        interval_seconds=settings.MAIL_DELIVERY_INTERVAL_SECONDS,
        run=run,
    )


def build_proposal_expiry_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Record every proposal whose book-by passed unfilled.

    **Idempotent and safe beside itself with no lock** (``docs/adr/0092``): the
    aggregate records nothing on a proposal already ended, a genuine race is
    caught by the stream version, and the loser steps over that one proposal and
    keeps going.

    **Correctness does not depend on it running**: a proposal is over from its
    book-by on at every read. What it buys is the record — silently, since the
    mechanics §5.4 tells nobody when a card simply disappears.
    """

    clock = build_clock()

    async def run() -> None:
        async with session_factory() as session:
            expired = await build_expire_proposals(session, clock=clock).execute()
        if expired.proposals or expired.conflicts:
            logger.info(
                "proposal expiry finished",
                extra={
                    "job": PROPOSAL_EXPIRY_JOB,
                    "proposals": expired.proposals,
                    "conflicts": expired.conflicts,
                },
            )

    return PeriodicJob(
        name=PROPOSAL_EXPIRY_JOB,
        interval_seconds=settings.PROPOSAL_EXPIRY_INTERVAL_SECONDS,
        run=run,
    )


def build_request_timeout_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Call off every request an On request club did not answer in time
    (the mechanics §16.8, §16.16).

    **Idempotent and safe beside itself with no lock**: each request is one
    transaction that locks its game first, the aggregate records nothing on a
    request already answered, and a genuine race is caught by the stream
    version and stepped over. **Correctness depends on it**: until it runs an
    unanswered request holds its court and owes its players nothing.
    """

    clock = build_clock()

    async def run() -> None:
        async with session_factory() as session:
            done = await build_expire_unanswered_requests(
                session, clock=clock, settings=settings
            ).execute()
        if done.requests or done.conflicts:
            logger.info(
                "request timeout finished",
                extra={
                    "job": REQUEST_TIMEOUT_JOB,
                    "requests": done.requests,
                    "conflicts": done.conflicts,
                },
            )

    return PeriodicJob(
        name=REQUEST_TIMEOUT_JOB,
        interval_seconds=settings.REQUEST_TIMEOUT_INTERVAL_SECONDS,
        run=run,
    )


def build_time_to_pay_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Run out every time to pay that is up (the mechanics §12.2, Q109).

    **Idempotent and safe beside itself with no lock**: each game is one
    transaction that locks it first, the aggregate records nothing on a time
    already run out or one still running, and a genuine race is caught by the
    stream version and stepped over. **Correctness depends on it**: until it
    runs, a seat whose time ran out is still its payer's alone, and the others'
    money stays held on their cards.
    """

    clock = build_clock()

    async def run() -> None:
        async with session_factory() as session:
            done = await build_run_out_the_time_to_pay(
                session, clock=clock, settings=settings
            ).execute()
        if done.games or done.conflicts:
            logger.info(
                "time to pay finished",
                extra={
                    "job": TIME_TO_PAY_JOB,
                    "games": done.games,
                    "conflicts": done.conflicts,
                },
            )

    return PeriodicJob(
        name=TIME_TO_PAY_JOB,
        interval_seconds=settings.TIME_TO_PAY_INTERVAL_SECONDS,
        run=run,
    )


def build_cut_off_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """At each booked game's cut-off, take the shares of a full game and call
    off one still short, letting every hold go (the mechanics §12.2, §12.3,
    §16.12, Q113; #544, #637).

    **Idempotent and safe beside itself with no lock**: each game is one
    transaction that locks it first, the aggregate records nothing on a game no
    longer short and takes nothing no longer held, and a genuine race is caught
    by the stream version and stepped over. **Correctness depends on it**:
    until it runs, a full game's shares are only held — its club has collected
    nothing — and the holds of a game called off at its cut-off are not let go.
    """

    clock = build_clock()

    async def run() -> None:
        async with session_factory() as session:
            done = await build_the_cut_off(
                session, clock=clock, settings=settings
            ).execute()
        if done.games or done.taken or done.conflicts:
            logger.info(
                "cut-off finished",
                extra={
                    "job": CUT_OFF_JOB,
                    "games": done.games,
                    "taken": done.taken,
                    "conflicts": done.conflicts,
                },
            )

    return PeriodicJob(
        name=CUT_OFF_JOB,
        interval_seconds=settings.CUT_OFF_INTERVAL_SECONDS,
        run=run,
    )


def build_holding_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """At each checked share's Holding time — four days before its game's
    cut-off — hold it on its card again, over the provider this process moves
    money through, and give a refused one's player their time to fix the card
    (the mechanics §12.2, Q113; #639).

    **Idempotent and safe beside itself with no lock**: each game is one
    transaction that locks it first, a share held already is no longer
    checked and is asked nothing again, a hold asked twice under one key is
    answered the first one's, and a genuine race is caught by the stream
    version and stepped over. **Correctness depends on it**: until it runs, a
    checked share is held nowhere.
    """

    clock = build_clock()
    provider = build_payment_provider(settings)

    async def run() -> None:
        async with session_factory() as session:
            done = await build_the_holding(
                session, clock=clock, provider=provider, settings=settings
            ).execute()
        if done.held or done.refused or done.conflicts:
            logger.info(
                "holding finished",
                extra={
                    "job": HOLDING_JOB,
                    "held": done.held,
                    "refused": done.refused,
                    "conflicts": done.conflicts,
                },
            )

    return PeriodicJob(
        name=HOLDING_JOB,
        interval_seconds=settings.HOLDING_INTERVAL_SECONDS,
        run=run,
    )


def build_how_did_it_go_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Ask all four *How did it go?* when a Competitive booked game's hour
    ends (#663).

    **Idempotent and safe beside itself with no lock**: a game's players are
    told under a key of the game's, on the day of its hour's end, so a second
    run tells nothing again — and two processes at once collide on a player's
    day, the second stepped over. **What it buys is the asking, not
    correctness**: a game waits for its score whether or not this has run.
    """

    clock = build_clock()

    async def run() -> None:
        async with session_factory() as session:
            done = await build_ask_how_did_it_go(session, clock=clock).execute()
        if done.games or done.conflicts:
            logger.info(
                "how did it go finished",
                extra={
                    "job": HOW_DID_IT_GO_JOB,
                    "games": done.games,
                    "conflicts": done.conflicts,
                },
            )

    return PeriodicJob(
        name=HOW_DID_IT_GO_JOB,
        interval_seconds=settings.HOW_DID_IT_GO_INTERVAL_SECONDS,
        run=run,
    )


def build_club_payouts_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Decide every club's payout for its games over once its day has closed
    (the mechanics §12.6, §16.11) — the outbox then makes it at the provider
    and tells the desk.

    **Idempotent and safe beside itself with no lock**: a club day's payout is
    one stream and a game is carried once, so a second process collides and is
    stepped over. **Correctness depends on it**: nothing else pays a club.
    """

    clock = build_clock()

    async def run() -> None:
        async with session_factory() as session:
            done = await build_decide_club_payouts(session, clock=clock).execute()
        if done.decided or done.conflicts:
            logger.info(
                "club payouts finished",
                extra={
                    "job": CLUB_PAYOUTS_JOB,
                    "decided": done.decided,
                    "conflicts": done.conflicts,
                },
            )

    return PeriodicJob(
        name=CLUB_PAYOUTS_JOB,
        interval_seconds=settings.CLUB_PAYOUTS_INTERVAL_SECONDS,
        run=run,
    )


def build_new_bookings_summary_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Email every club's desk the games booked at it in the day that just
    closed (the mechanics §16.12, *a daily summary*).

    **Idempotent and safe beside itself with no lock**: a club's day is summed
    up in a stream of its own, born with the email in one transaction, so a
    second process collides on it and its email is rolled back with it.
    """

    clock = build_clock()

    async def run() -> None:
        async with session_factory() as session:
            done = await build_summarise_new_bookings(
                session, clock=clock, settings=settings
            ).execute()
        if done.clubs or done.conflicts:
            logger.info(
                "new bookings summary finished",
                extra={
                    "job": NEW_BOOKINGS_SUMMARY_JOB,
                    "clubs": done.clubs,
                    "conflicts": done.conflicts,
                },
            )

    return PeriodicJob(
        name=NEW_BOOKINGS_SUMMARY_JOB,
        interval_seconds=settings.NEW_BOOKINGS_SUMMARY_INTERVAL_SECONDS,
        run=run,
    )


def build_proposer_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Walk every pool and deal what its free court hours and free, fitting
    members make — the sweep that guarantees a change is dealt from.

    **Idempotent and safe beside itself with no lock**: a batch deals nothing a
    game already holds, a pick's id is its game so a second process making it
    collides on the stream, and a deal the world moved past is refused by the
    dealer's own act and counted. **One pool failing is logged and passed
    over**, so a pool nobody can deal to never stops the others being dealt.
    """

    clock = build_clock()

    async def run() -> None:
        async with session_factory() as session:
            proposer = build_propose_games(session, clock=clock)
            done = await propose_over(
                session, proposer, await proposer.every_pool(), job=PROPOSER_JOB
            )
        _log_proposed(PROPOSER_JOB, done)

    return PeriodicJob(
        name=PROPOSER_JOB,
        interval_seconds=settings.PROPOSER_INTERVAL_SECONDS,
        run=run,
    )


def build_proposer_on_changes_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    due: DueForProposing,
) -> PeriodicJob:
    """Deal in the pools a change delivered in this process made due, seconds
    after it — the same batch as the sweep's, over fewer pools. A tick with
    nothing due opens no session."""

    clock = build_clock()

    async def run() -> None:
        changed = due.take()
        if not changed.anything:
            return
        async with session_factory() as session:
            proposer = build_propose_games(session, clock=clock)
            done = await propose_over(
                session,
                proposer,
                await proposer.pools_due(changed),
                job=PROPOSER_ON_CHANGES_JOB,
            )
        _log_proposed(PROPOSER_ON_CHANGES_JOB, done)

    return PeriodicJob(
        name=PROPOSER_ON_CHANGES_JOB,
        interval_seconds=settings.PROPOSER_ON_CHANGES_INTERVAL_SECONDS,
        run=run,
    )


async def propose_over(
    session: AsyncSession, proposer: ProposeGames, pools: Sequence[UUID], *, job: str
) -> Proposed:
    """The proposer's unit of work over these pools, one after another — the
    sweep's and the short tick's, and the console's *Run it now*
    (``app/api/dev/jobs.py``), which hands it this request's session and clock.
    One pool failing is rolled back, logged and passed over."""

    done = Proposed()
    for pool_id in pools:
        try:
            done += await proposer.execute(pool_id)
        except Exception:
            await session.rollback()
            logger.exception(
                "proposer failed on a pool", extra={"job": job, "pool_id": str(pool_id)}
            )
    return done


def _log_proposed(job: str, done: Proposed) -> None:
    if done.anything:
        logger.info(
            "proposer finished",
            extra={
                "job": job,
                "pools": done.pools,
                "made": done.made,
                "dealt": done.dealt,
                "lost": done.lost,
                "redealt": done.redealt,
                "refused": done.refused,
            },
        )


def build_rating_catch_up_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Move every Level a confirmed result has tested and nothing has applied.

    **The one loop here that correctness depends on.** Every other job buys a
    record, or a table the size of what is live; this one is the only path a
    result settled by a window closing has to a rating, because
    ``docs/adr/0137`` refused a ``ResultConfirmed`` event and recorded that cost
    by name. A player whose game confirmed on Tuesday keeps Monday's Level until
    this runs — within the minute (#654). An agreement's game is usually moved
    already, from the outbox, and the walk steps over it.

    **Idempotent and safe beside itself with no lock** (``docs/adr/0092``): every
    move records the game that caused it, so a rating that has already folded a
    result skips it inside the aggregate and a second pass appends nothing. A
    genuine race is caught by the stream version, and the loser **steps over that
    one game and keeps going** — every process walks the same clock-derived list
    in the same order, so a run that ended on its first conflict would be a loop
    that made no progress in any process.

    **It holds no cursor**, which is what makes a half-finished run a non-event:
    the next tick re-derives the whole walk from the clock and finds exactly the
    results nobody has folded.
    """

    async def run() -> None:
        async with session_factory() as session:
            settled = await build_settle_ratings_on_results(session).execute()
        logger.info(
            "rating catch-up finished",
            extra={
                "job": RATING_CATCH_UP_JOB,
                "games": settled.games,
                "ratings": settled.ratings,
                # *Nobody played* and *everybody who played was unrated in that
                # sport* both show up as nothing moving, and only one of them is
                # a defect.
                "unrated_seats": settled.unrated,
                "conflicts": settled.conflicts,
            },
        )

    return PeriodicJob(
        name=RATING_CATCH_UP_JOB,
        interval_seconds=settings.RATING_CATCH_UP_INTERVAL_SECONDS,
        run=run,
    )


def build_conversation_sweep_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> PeriodicJob:
    """Destroy every room whose episode is over. **Destroyed, not delisted.**

    **Correctness does not depend on it running** (``docs/adr/0153`` §5). A room's
    end is a fold over its own stream, so every route on it already answers
    ``conversation_not_found`` past that instant and every list has already
    dropped it. What the loop buys is that the destruction is **real** — the
    entries stop existing rather than stopping being answered with — which is the
    difference between a room that is over and a record with no end.

    **Idempotent and safe beside itself with no lock** (``docs/adr/0092``):
    destroying a room twice destroys it once, and two processes racing over the
    same walk leave what one leaves. *N processes, N runs* costs a repeated fold.

    **It holds no cursor**, because there is no position to lose: the walk is the
    whole table and the decision is a fold, so a run that dies half way is
    re-derived in full by the next tick.
    """

    clock = build_clock()

    async def run() -> None:
        async with session_factory() as session:
            swept = await build_destroy_ended_conversations(
                session, clock=clock
            ).execute()
        logger.info(
            "conversation sweep finished",
            extra={
                "job": CONVERSATION_SWEEP_JOB,
                # Both numbers, because *the loop is off* and *the loop is
                # running and nothing has ended* have one symptom — rooms
                # accumulating — and only one of them is somebody's problem.
                "rooms": swept.walked,
                "destroyed": swept.destroyed,
            },
        )

    return PeriodicJob(
        name=CONVERSATION_SWEEP_JOB,
        interval_seconds=settings.CONVERSATION_SWEEP_INTERVAL_SECONDS,
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


def build_photo_review_backfill(*, settings: Settings) -> PeriodicJob:
    """Ask the reviewer about the photos nobody ever asked it about (#197).

    **Idempotent and safe beside itself with no lock** (``docs/adr/0092``): two
    runs handed the same photo both ask and both write the same-shaped metadata,
    and the loser overwrites a verdict with a verdict. The bytes are never
    touched by either. What *N* processes cost here is duplicated inference
    rather than a wrong answer, which is why the budget is small and the
    interval is not — see `Settings` for both numbers, and the use case for why
    neither of them can change which photos are chosen.

    The reviewer is built from the composition root, so this job asks the same
    sidecar the upload path asks and applies the same rule
    (``domain/photos.py`` — `verdict_from_similarities`). **A batch with its own
    copy of the threshold would be a second reviewer**, able to disagree with
    the upload path about one image with nothing downstream to say which was
    right.
    """

    storage = build_photo_storage(settings)
    transcoder = build_image_transcoder()
    review = build_photo_review(settings)

    async def run() -> None:
        report = await ReviewUnreviewedPhotos(
            storage=storage,
            transcoder=transcoder,
            review=review,
            batch_limit=settings.PHOTO_REVIEW_BACKFILL_BATCH_LIMIT,
            pause_seconds=settings.PHOTO_REVIEW_BACKFILL_PAUSE_SECONDS,
        ).execute()

        # At ``WARNING`` when the reviewer would not answer — whether it gave
        # up the run or refused individual photos — because that is the state
        # where the loop is running, finding work and fixing nothing, which at
        # ``INFO`` beside a `photos_updated` of zero is indistinguishable from a
        # corpus that is already done.
        logger.log(
            logging.WARNING
            if report.stopped_unreviewable or report.refused
            else logging.INFO,
            "photo review backfill finished",
            extra={
                "job": PHOTO_REVIEW_BACKFILL_JOB,
                "photos_examined": report.examined,
                "photos_updated": report.updated,
                "photos_vanished": report.vanished,
                "photos_unreadable": report.unreadable,
                "photos_refused": report.refused,
                # Population 3, which this job deliberately does not touch. It
                # is here because a count is what makes *is it worth re-running
                # the corpus against the new prompts* answerable at all.
                "photos_against_a_superseded_prompt_set": report.superseded,
                "stopped_on_budget": report.stopped_on_budget,
                "reviewer_unavailable": (
                    report.unavailable.value
                    if report.unavailable is not None
                    else None
                ),
            },
        )

    return PeriodicJob(
        name=PHOTO_REVIEW_BACKFILL_JOB,
        interval_seconds=settings.PHOTO_REVIEW_BACKFILL_INTERVAL_SECONDS,
        run=run,
    )
