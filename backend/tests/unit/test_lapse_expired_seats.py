"""The sweep that makes a lapse a fact somebody can count.

**It buys the record, not correctness** (#252). Every read in this context is
bounded by ``now`` — a seat past its day reads as lapsed, its pair releases and
its challenge stands as ``LAPSED`` whether or not anything has been past — so
what these cases assert is the thing the reads cannot buy later: a ``SeatLapsed``
in the log, so that *answers challenges* has a denominator.

Run against the **real** adapter and a real (SQLite) session rather than a
double, because the half worth asserting is exactly the half a double would
invent: which streams the loop even looks at. A seat's deadline is its seating
event plus the window that stood when it was invited, so *every challenge opened
at or before ``now`` minus the shortest window this log has ever stamped* is the
candidate set — a claim about the store, not about the aggregate.

**And the window has moved once already** (``docs/adr/0151``), which is what the
last two cases here are for: a seat is swept at *its own* deadline whichever
window stamped it, so a change to the number cannot leave the record late for the
seats in flight across it.

**A lapse is not a decline**, and this file is where that stops being a comment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlalchemy import select

from app.application.events import EventStreamVersionConflict

from app.bootstrap.composition import (
    build_challenge_repository,
    build_domain_event_store,
    build_event_publisher,
    build_lapsing_challenge_query,
    build_open_challenge_query,
    build_unit_of_work,
)
from app.engines.matchfit.core import SearchMode
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Instant, Sport, instant
from app.modules.challenges.application.lapse_expired_seats import (
    LapseExpiredSeats,
    Swept,
)
from app.modules.challenges.domain import answer_window
from app.modules.challenges.domain.answer_window import (
    ANSWER_WINDOW,
    SHORTEST_WINDOW_EVER_STAMPED,
    WINDOWS_EVER_STAMPED,
)
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.seats import SeatAnswer, SeatPlan, Side
from app.modules.challenges.domain.standing import Standing
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.player_profile.domain.availability import Window
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import CountingUnitOfWork

ORGANISER = new_uuid()
ALICE = new_uuid()
BOB = new_uuid()
CAROL = new_uuid()
SEARCH = new_uuid()


def at(hours: int = 0) -> Instant:
    return instant(
        datetime(2026, 8, 30, 12, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


SENT_AT = at(0)
INSIDE = at(1)
OUTSIDE = instant(SENT_AT + ANSWER_WINDOW + timedelta(minutes=1))


class FrozenClock:
    def __init__(self, at: Instant) -> None:
        self._at = at

    def now(self) -> datetime:
        return self._at


def invited(player_id, side: Side, position: int) -> SeatPlan:
    return SeatPlan(
        side=side,
        player_id=player_id,
        origin=SentFromSearch(search_id=SEARCH, position=position),
    )


def a_tennis_challenge(*, organiser=ORGANISER, invitee=ALICE) -> Challenge:
    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.TENNIS,
        mode=SearchMode.FOR_FUN,
        window=Window.ANY,
        organiser_id=organiser,
        arrangement=(
            SeatPlan(side=Side.A, player_id=organiser),
            invited(invitee, Side.B, 1),
        ),
        occurred_at=SENT_AT,
    )


def a_padel_challenge() -> Challenge:
    return Challenge.sent(
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        mode=SearchMode.FOR_FUN,
        window=Window.WEEKEND,
        organiser_id=ORGANISER,
        arrangement=(
            SeatPlan(side=Side.A, player_id=ORGANISER),
            invited(ALICE, Side.A, 1),
            invited(BOB, Side.B, 2),
            invited(CAROL, Side.B, 3),
        ),
        occurred_at=SENT_AT,
    )


def _repository(session):
    return build_challenge_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


async def _record(session, challenge: Challenge) -> Challenge:
    """Write a challenge the way a request would, and commit it."""

    await _repository(session).save(challenge)
    await session.commit()
    return challenge


def _sweep(session, *, now: Instant) -> LapseExpiredSeats:
    return LapseExpiredSeats(
        clock=FrozenClock(now),
        challenges=_repository(session),
        lapsing=build_lapsing_challenge_query(session),
        unit_of_work=build_unit_of_work(session),
    )


async def _lapses_in(session, challenge_id) -> int:
    """How many ``SeatLapsed`` rows that challenge's stream holds."""

    rows = await session.execute(
        select(EventStoreORM.event_type).where(
            EventStoreORM.aggregate_id == challenge_id
        )
    )
    return sum(1 for event_type in rows.scalars().all() if "lapsed" in event_type)


async def _reload(session, challenge_id) -> Challenge:
    reloaded = await _repository(session).load(challenge_id)
    assert reloaded is not None
    return reloaded


# ---------------------------------------------------------------------------
# What one sweep records
# ---------------------------------------------------------------------------


async def test_the_sweep_records_a_seat_whose_window_passed(session_factory):
    async with session_factory() as session:
        challenge = await _record(session, a_tennis_challenge())

        swept = await _sweep(session, now=OUTSIDE).execute()

        assert swept == Swept(seats=1, challenges=1, conflicts=0)
        assert await _lapses_in(session, challenge.id) == 1


async def test_a_lapsed_seat_is_recorded_as_a_lapse_and_never_as_a_decline(
    session_factory,
):
    """The whole reason the sweep exists rather than a status column being set.

    *answers challenges* is a Strand over challenges that got an answer inside
    their window, and it is unmeasurable if silence is filed as judgement.
    """

    async with session_factory() as session:
        challenge = await _record(session, a_tennis_challenge())

        await _sweep(session, now=OUTSIDE).execute()

        reloaded = await _reload(session, challenge.id)
        (seat,) = [seat for seat in reloaded.seats if seat.holds(ALICE)]
        assert seat.answer is SeatAnswer.LAPSED
        assert reloaded.standing_at(OUTSIDE) is Standing.LAPSED


async def test_nothing_is_recorded_while_the_window_still_stands(session_factory):
    async with session_factory() as session:
        challenge = await _record(session, a_tennis_challenge())

        swept = await _sweep(session, now=INSIDE).execute()

        assert swept == Swept(seats=0, challenges=0, conflicts=0)
        assert await _lapses_in(session, challenge.id) == 0


async def test_a_second_sweep_appends_nothing(session_factory):
    """Idempotent and safe beside itself with no lock (``docs/adr/0092``).

    With N API processes the loop runs N times per interval at unrelated
    moments, so *the second run* is not a hypothetical — it is what the
    deployment does.
    """

    async with session_factory() as session:
        challenge = await _record(session, a_tennis_challenge())
        await _sweep(session, now=OUTSIDE).execute()

        swept = await _sweep(session, now=OUTSIDE).execute()

        assert swept == Swept(seats=0, challenges=0, conflicts=0)
        assert await _lapses_in(session, challenge.id) == 1


async def test_an_answered_seat_is_left_alone(session_factory):
    """A decline is a judgement and stays one; only silence lapses."""

    async with session_factory() as session:
        challenge = a_padel_challenge()
        challenge.accept(ALICE, occurred_at=INSIDE)
        challenge.decline(BOB, occurred_at=INSIDE)
        await _record(session, challenge)

        swept = await _sweep(session, now=OUTSIDE).execute()

        assert swept.seats == 1
        reloaded = await _reload(session, challenge.id)
        answers = {
            seat.player_id: seat.answer
            for seat in reloaded.seats
            if seat.player_id is not None
        }
        assert answers == {
            ORGANISER: SeatAnswer.ACCEPTED,
            ALICE: SeatAnswer.ACCEPTED,
            BOB: SeatAnswer.DECLINED,
            CAROL: SeatAnswer.LAPSED,
        }


async def test_one_lapse_among_live_seats_does_not_end_the_challenge(session_factory):
    """One lapse among accepted seats reads `LINE_UP_INCOMPLETE`.

    The state the builder is re-entered from, and **not a waiting room**: the
    people who are in are in, and a conversation between them has already
    started. The seat the silence emptied is simply open again.
    """

    async with session_factory() as session:
        challenge = a_padel_challenge()
        challenge.accept(ALICE, occurred_at=INSIDE)
        challenge.accept(BOB, occurred_at=INSIDE)
        await _record(session, challenge)

        swept = await _sweep(session, now=OUTSIDE).execute()

        assert swept == Swept(seats=1, challenges=1, conflicts=0)
        reloaded = await _reload(session, challenge.id)
        assert reloaded.standing_at(OUTSIDE) is Standing.LINE_UP_INCOMPLETE


async def test_a_mutual_born_challenge_has_no_window_to_pass(session_factory):
    """Both seats accepted from birth and no deadline anywhere on it.

    It is a candidate the moment it is a day old — the loop's read is about the
    *store* and cannot see a deadline — and the aggregate records nothing, which
    is where the over-reading is paid for and why it is safe.
    """

    async with session_factory() as session:
        challenge = await _record(
            session,
            Challenge.opened_from_mutual_interest(
                challenge_id=new_uuid(),
                sport=Sport.TENNIS,
                organiser_id=ORGANISER,
                other_player_id=ALICE,
                occurred_at=SENT_AT,
            ),
        )

        swept = await _sweep(session, now=OUTSIDE).execute()

        assert swept == Swept(seats=0, challenges=0, conflicts=0)
        assert await _lapses_in(session, challenge.id) == 0


async def test_the_sweep_changes_no_reading(session_factory):
    """The gate answers the same either side of it, which is the whole claim.

    A reader asking *is this challenge still open* between a deadline and a sweep
    must get the same answer either way.
    """

    async with session_factory() as session:
        await _record(session, a_tennis_challenge())
        query = build_open_challenge_query(session)
        before = await query.open_pairs_among([ORGANISER, ALICE], now=OUTSIDE)

        await _sweep(session, now=OUTSIDE).execute()

        assert before == frozenset()
        assert await query.open_pairs_among([ORGANISER, ALICE], now=OUTSIDE) == before


# ---------------------------------------------------------------------------
# Which streams the loop looks at
# ---------------------------------------------------------------------------


async def test_a_challenge_younger_than_the_window_is_not_a_candidate(session_factory):
    """The one thing the read narrows on, and the window it narrows with.

    A seat's deadline is its seating event plus the window that stood when it was
    invited, so a challenge opened after ``now`` minus the **shortest** window
    this log has ever stamped holds no seat that could have lapsed under any of
    them — and a loop that read it anyway would grow with every send rather than
    with the backlog.

    The cutoff is deliberately not ``ANSWER_WINDOW``. Today's number applied to
    yesterday's seats **under-names**: every seat still running on a shorter
    window lapses before a cutoff written from the longer one goes looking for
    it, which is the failure the two cases below drive.
    """

    now = instant(SENT_AT + ANSWER_WINDOW + timedelta(hours=1))
    async with session_factory() as session:
        old = await _record(session, a_tennis_challenge())
        young = await _record(
            session,
            Challenge.sent(
                challenge_id=new_uuid(),
                sport=Sport.TENNIS,
                mode=SearchMode.FOR_FUN,
                window=Window.ANY,
                organiser_id=ORGANISER,
                arrangement=(
                    SeatPlan(side=Side.A, player_id=ORGANISER),
                    invited(BOB, Side.B, 1),
                ),
                occurred_at=instant(
                    now - SHORTEST_WINDOW_EVER_STAMPED + timedelta(minutes=1)
                ),
            ),
        )

        candidates = await build_lapsing_challenge_query(session).may_have_lapsed(
            now=now
        )

        assert candidates == (old.id,)
        assert young.id not in candidates


def test_the_ledger_still_carries_every_window_this_repository_has_shipped():
    """The one thing about the ledger a test can know: what is already in the log.

    ``WINDOWS_EVER_STAMPED`` is a claim about **history**, and nothing in a
    running process can tell you what a seat committed last month was stamped
    with. What a test can hold is that the values this repository has actually
    shipped are still in it — #217's day, and today's two.

    It exists for the one way the ledger can be mismaintained without going red
    anywhere else: a future lengthening that **replaces** the old value instead
    of appending it. ``min`` would then move up with the constant, the sweep
    would narrow past every seat still running on the shorter window, and the
    record would be late for all of them — the exact failure this cutoff was
    introduced to end.
    """

    assert timedelta(hours=24) in WINDOWS_EVER_STAMPED
    assert ANSWER_WINDOW in WINDOWS_EVER_STAMPED
    assert SHORTEST_WINDOW_EVER_STAMPED == min(WINDOWS_EVER_STAMPED)


def _sent_under(window, *, invitee=ALICE) -> Challenge:
    """A challenge whose invited seat is stamped with ``window`` rather than today's.

    The stamp is the whole point: ``answer_by`` is written onto the seat when the
    seat is invited and folded back off the stream, so a seat sent before the
    number moved keeps the promise it was sent with. Patching the constant for
    the length of the send is how a stream from another era is written without
    hand-forging an event.
    """

    with pytest.MonkeyPatch.context() as era:
        era.setattr(answer_window, "ANSWER_WINDOW", window)
        return a_tennis_challenge(invitee=invitee)


async def test_a_seat_on_the_window_that_has_since_lengthened_is_swept_on_time(
    session_factory,
):
    """A shorter stamp than today's, swept at **its own** deadline.

    This is the live case: the window became forty-eight hours
    (``docs/adr/0151``) while seats stamped with the old twenty-four were still
    running. A cutoff written from today's number goes looking for them a whole
    day after they ran out, and the ``SeatLapsed`` that *answers challenges*
    counts is written a day late for every one of them — a denominator that was
    wrong for as long as it took, on a loop whose entire job is the record.
    """

    stamped = SHORTEST_WINDOW_EVER_STAMPED
    assert stamped < ANSWER_WINDOW, "this case needs a window shorter than today's"

    challenge = _sent_under(stamped)
    its_own_deadline = instant(SENT_AT + stamped + timedelta(minutes=1))

    async with session_factory() as session:
        await _record(session, challenge)

        candidates = await build_lapsing_challenge_query(session).may_have_lapsed(
            now=its_own_deadline
        )
        assert candidates == (challenge.id,)

        swept = await _sweep(session, now=its_own_deadline).execute()
        assert swept == Swept(seats=1, challenges=1, conflicts=0)


async def test_a_seat_on_a_window_that_has_since_shortened_is_still_swept(
    session_factory,
):
    """A longer stamp than today's, and the sweep still names it.

    The mirror of the case above, and the one a future **shortening** puts every
    outstanding seat into at once: they keep the longer promise they were sent
    with, and the cutoff has to reach them anyway.

    **This one pins a property rather than reproducing a bug, and it says so
    because the difference matters.** ADR-0151 §7 reads the asymmetry the other
    way round — *"survives lengthening and would not have survived shortening"* —
    and the predicate does not agree: ``occurred_at <= now - W`` is monotone in
    ``now`` and holds no cursor, so a stream that qualifies once qualifies for
    ever and the only thing any window can cost is **lateness**. A shortening
    makes the cutoff *wider*, which over-names and is free; it was the lengthening
    above that had a bug. So there is no shortening regression to drive, and what
    is asserted instead is the invariant that would make one impossible if the
    ledger were ever mismaintained: the sweep never narrows on a window longer
    than one a live seat carries.
    """

    stamped = ANSWER_WINDOW * 2
    challenge = _sent_under(stamped)
    still_running = instant(SENT_AT + ANSWER_WINDOW + timedelta(hours=1))
    its_own_deadline = instant(SENT_AT + stamped + timedelta(minutes=1))

    async with session_factory() as session:
        await _record(session, challenge)

        # A candidate long before it owes anything — over-naming, and free.
        assert await build_lapsing_challenge_query(session).may_have_lapsed(
            now=still_running
        ) == (challenge.id,)
        early = await _sweep(session, now=still_running).execute()
        assert early == Swept(seats=0, challenges=0, conflicts=0)

        assert await build_lapsing_challenge_query(session).may_have_lapsed(
            now=its_own_deadline
        ) == (challenge.id,)
        swept = await _sweep(session, now=its_own_deadline).execute()
        assert swept == Swept(seats=1, challenges=1, conflicts=0)


# ---------------------------------------------------------------------------
# Racing another copy of the same loop
#
# ``docs/adr/0092`` puts a copy of every job in every API process with no lock
# between them, and this loop's candidate list is derived from the clock — so N
# processes walk the **same** challenges in the **same** order. These two cases
# are about the one thing that makes that survivable: a conflict costs one
# challenge, never the run.
# ---------------------------------------------------------------------------


@dataclass
class StubLapsing:
    """The candidate list, stated rather than read off a store."""

    ids: tuple[UUID, ...]

    async def may_have_lapsed(self, *, now: Instant) -> tuple[UUID, ...]:
        return self.ids


@dataclass
class StubChallenges:
    """Challenges in memory, with some of their streams already taken.

    ``taken`` is the other process: a stream it appended to between this run's
    load and its own append, which is exactly what the store answers with an
    ``EventStreamVersionConflict``.
    """

    challenges: dict[UUID, Challenge]
    taken: frozenset[UUID] = frozenset()
    saved: list[UUID] = field(default_factory=list)

    async def load(self, challenge_id: UUID) -> Challenge | None:
        return self.challenges.get(challenge_id)

    async def save(self, challenge: Challenge) -> None:
        if challenge.id in self.taken:
            raise EventStreamVersionConflict("somebody appended first")
        self.saved.append(challenge.id)


async def test_a_lost_race_costs_one_challenge_and_not_the_run():
    """The run keeps going, and the loss is counted rather than swallowed.

    Every process walks this list in this order, so a run that ended on its
    first conflict would be a loop that made no progress in **any** process —
    each of them stopping at the same challenge, for ever.
    """

    lost, won = a_tennis_challenge(), a_tennis_challenge(invitee=BOB)
    challenges = StubChallenges(
        challenges={lost.id: lost, won.id: won}, taken=frozenset({lost.id})
    )
    uow = CountingUnitOfWork()

    swept = await LapseExpiredSeats(
        clock=FrozenClock(OUTSIDE),
        challenges=challenges,
        lapsing=StubLapsing((lost.id, won.id)),
        unit_of_work=uow,
    ).execute()

    assert swept == Swept(seats=1, challenges=1, conflicts=1)
    assert challenges.saved == [won.id]


async def test_each_challenge_is_its_own_transaction():
    """One commit per challenge written down, and a rollback for the one lost.

    The boundary is per **item** rather than per run because nothing a lapse
    touches spans two streams: a batch-wide transaction would buy no consistency
    anybody wanted and would cost the run its first conflict.
    """

    lost, won = a_tennis_challenge(), a_tennis_challenge(invitee=BOB)
    uow = CountingUnitOfWork()

    await LapseExpiredSeats(
        clock=FrozenClock(OUTSIDE),
        challenges=StubChallenges(
            challenges={lost.id: lost, won.id: won}, taken=frozenset({lost.id})
        ),
        lapsing=StubLapsing((lost.id, won.id)),
        unit_of_work=uow,
    ).execute()

    assert (uow.commits, uow.rollbacks) == (1, 1)
