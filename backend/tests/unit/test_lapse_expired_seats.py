"""The sweep that makes a lapse a fact somebody can count.

**It buys the record, not correctness** (#252). Every read in this context is
bounded by ``now`` — a seat past its day reads as lapsed, its pair releases and
its challenge stands as ``LAPSED`` whether or not anything has been past — so
what these cases assert is the thing the reads cannot buy later: a ``SeatLapsed``
in the log, so that *answers challenges* has a denominator.

Run against the **real** adapter and a real (SQLite) session rather than a
double, because the half worth asserting is exactly the half a double would
invent: which streams the loop even looks at. A seat's deadline is its seating
event plus the answer window and nothing else, so *every challenge opened at or
before ``now`` minus a day* is the candidate set — a claim about the store, not
about the aggregate.

**A lapse is not a decline**, and this file is where that stops being a comment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

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
from app.modules.challenges.domain.answer_window import ANSWER_WINDOW
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
    """The one thing the read narrows on, and it narrows on it exactly.

    A seat's deadline is its seating event plus the answer window, so a challenge
    opened after ``now`` minus a day has no seat that could have lapsed — and a
    loop that read it anyway would grow with every send rather than with the
    backlog.
    """

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
                occurred_at=at(2),
            ),
        )

        candidates = await build_lapsing_challenge_query(session).may_have_lapsed(
            now=instant(SENT_AT + ANSWER_WINDOW + timedelta(hours=1))
        )

        assert candidates == (old.id,)
        assert young.id not in candidates


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
