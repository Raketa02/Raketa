"""The schedule is a column, and every write arms it.

ADR-0076 and `Raketa02/Raketa#72`. `test_next_wake.py` asserts what the kernel
*says*; this asserts what is **stored** — over the real Clubs, Courts and Matches
contexts, the real repository and a real (SQLite) session, with only the clock in
the test's hand.

**The claim under all of it is one sentence: the stored moment is the moment the
kernel would compute for the stored record.** Not *a* moment, not *the moment the
writer had in mind* — those two disagree the instant somebody adds a use case and
forgets. So the assertion is written as an equality against `kernel.next_wake`
run over the row that was just read back, and it is made after every kind of
write there is.

**And the boundary set is a function of the record, not of the calendar**, which
is why *recomputed on every write* is stronger than *recomputed when a threshold
moves*: a match on two paid seats wakes at T-12h, and the same match after a
third payment wakes at T-4h without a single deadline having changed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.bootstrap.composition import (
    build_club_repository,
    build_court_holds,
    build_event_publisher,
    build_match_repository,
    build_match_schedule,
    build_reservation_repository,
    build_unit_of_work,
)
from app.kernel import (
    Cover,
    Boundary,
    SeatShare,
    Sport,
    WakeReason,
    grosze,
    hours,
    instant,
    live_outcome,
    next_wake,
    zloty,
)
from app.modules.clubs.application.add_court import AddCourt
from app.modules.clubs.application.add_court_category import AddCourtCategory
from app.modules.clubs.application.commands import (
    AddCourtCategoryCommand,
    AddCourtCommand,
    RegisterClubCommand,
)
from app.modules.clubs.application.register_club import RegisterClub
from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.value_objects import (
    CategoryName,
    ClubName,
    ClubPricing,
    CourtLabel,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
)
from app.modules.courts.application.claim_court import ClaimCourt
from app.modules.matches.application.cancel_match import CancelMatch
from app.modules.matches.application.commands import (
    CancellationCause,
    CancelMatchCommand,
    MoveMatchStartCommand,
    PaySeatCommand,
    PostMatchCommand,
    TakeSeatCommand,
    DepartCommand,
)
from app.modules.matches.application.post_match import PostMatch
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.application.seat_moves import (
    MoveMatchStart,
    PaySeat,
    TakeSeat,
    Depart,
)
from app.modules.matches.infrastructure.sqlalchemy_match_models import MatchORM

START = instant(datetime(2026, 9, 8, 18, tzinfo=timezone.utc))
PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)


class _Clock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, moment) -> None:
        self._now = moment


class _World:
    def __init__(self, session, clock) -> None:
        clubs = build_club_repository(session)
        reservations = build_reservation_repository(session)
        matches = build_match_repository(
            session, events=build_event_publisher(session), clock=clock
        )
        uow = build_unit_of_work(session)
        holds = ResolveCourtHold(
            matches,
            build_court_holds(ClaimCourt(clubs, reservations, uow), reservations),
            uow,
            clock,
        )

        self.session = session
        self.clock = clock
        self.matches = matches
        self.schedule = build_match_schedule(session)
        self.register_club = RegisterClub(clubs, uow, clock)
        self.add_category = AddCourtCategory(clubs, uow, clock)
        self.add_court = AddCourt(clubs, uow, clock)
        self.post = PostMatch(matches, clubs, holds, uow, clock)
        self.move = MoveMatchStart(matches, holds, uow, clock)
        self.take = TakeSeat(matches, holds, uow, clock)
        self.pay = PaySeat(matches, holds, uow, clock)
        self.depart = Depart(matches, holds, uow, clock)
        self.cancel = CancelMatch(matches, holds, uow, clock)

    async def leave(self, match_id, player_id):
        """A departure at whatever the record says leaving is worth right now.

        The quote is the caller's (ADR-0033) and these suites are not about it,
        so it is read off the live record — which is what the departure route
        will do. ``tests/unit/test_match_departures.py`` is where a **stale**
        quote is the subject.
        """

        current = await self.matches.get(match_id)
        assert current is not None
        return await self.depart.execute(
            DepartCommand(
                match_id=match_id,
                player_id=player_id,
                quote=live_outcome(current.as_record(), instant(self.clock.now())),
            )
        )

    async def stored_schedule(self, match_id) -> tuple[object, object]:
        """The two columns, straight off the row — never through the aggregate.

        Read as columns deliberately: the aggregate does not carry them, and it
        must not start to. They are internal to the timekeeper (ADR-0076), and
        an aggregate that held them would be one line from putting them on a
        card.
        """

        row = (
            await self.session.execute(
                select(MatchORM.next_wake_at, MatchORM.wake_reason).where(
                    MatchORM.id == match_id
                )
            )
        ).one()
        return row.next_wake_at, row.wake_reason

    async def assert_armed_as_the_kernel_would(self, match_id) -> None:
        """The whole claim, in one call: stored == derived, for this record."""

        stored = await self.matches.get(match_id)
        assert stored is not None
        expected = next_wake(stored.as_record(), instant(self.clock.now()))
        at_column, reason_column = await self.stored_schedule(match_id)

        if expected is None:
            assert at_column is None and reason_column is None
            return
        assert at_column is not None
        assert instant(at_column.replace(tzinfo=timezone.utc)) == expected.at
        assert reason_column == expected.reason.value


@pytest.fixture
def clock():
    return _Clock(START - timedelta(days=14))


@pytest.fixture
async def world(session_factory, clock):
    async with session_factory() as session:
        yield _World(session, clock)


async def a_match(world, *, courts: int = 2, policy=None, **overrides):
    club = await world.register_club.execute(
        RegisterClubCommand(
            name=ClubName(f"Zabłocie {uuid4().hex[:6]}"),
            address=StreetAddress(
                line="ul. Zabłocie 25", city="Kraków", postal_code="30-701"
            ),
            point=GeoPoint(
                latitude=Decimal("50.048100"), longitude=Decimal("19.958500")
            ),
            timezone="Europe/Warsaw",
            policy=policy or ClubPolicy(),
            payout=PAYOUT,
            pricing=ClubPricing(),
        )
    )
    category = await world.add_category.execute(
        AddCourtCategoryCommand(
            club_id=club.id,
            name=CategoryName("Padel · indoor"),
            sport=Sport.PADEL,
            cover=Cover.INDOOR,
            rate=zloty(120),
        )
    )
    for index in range(courts):
        await world.add_court.execute(
            AddCourtCommand(
                club_id=club.id,
                category_id=category.id,
                label=CourtLabel(f"Court {index + 1}"),
            )
        )
    facts = dict(
        club_id=club.id,
        category_id=category.id,
        sport=Sport.PADEL,
        start=START,
        duration=hours(1),
        share=SeatShare(grosze(3800)),
    )
    facts.update(overrides)
    return await world.post.execute(PostMatchCommand(**facts))


async def seated(world, match, count: int, *, paid: int | None = None):
    players = [uuid4() for _ in range(count)]
    for player in players:
        await world.take.execute(TakeSeatCommand(match_id=match.id, player_id=player))
    for player in players[: count if paid is None else paid]:
        await world.pay.execute(PaySeatCommand(match_id=match.id, player_id=player))
    return players


# --- every write arms it ----------------------------------------------------


async def test_posting_a_match_arms_its_schedule(world):
    """`add` goes through the same column set `save` does, so the first write is
    not the one that has to be remembered separately."""

    match = await a_match(world)

    await world.assert_armed_as_the_kernel_would(match.id)
    at_column, reason = await world.stored_schedule(match.id)
    assert at_column is not None
    assert reason == WakeReason.COMMITMENT.value


async def test_every_kind_of_write_leaves_the_schedule_agreeing_with_the_record(world):
    """Taking, paying, moving the hour, vacating — the whole write vocabulary.

    Asserted after each one rather than at the end, because the failure being
    looked for is a *single* use case that forgets, and a final check would be
    satisfied by any later write repairing it.
    """

    match = await a_match(world)
    await world.assert_armed_as_the_kernel_would(match.id)

    players = await seated(world, match, 2, paid=0)
    await world.assert_armed_as_the_kernel_would(match.id)

    await world.pay.execute(
        PaySeatCommand(match_id=match.id, player_id=players[0])
    )
    await world.assert_armed_as_the_kernel_would(match.id)

    await world.pay.execute(
        PaySeatCommand(match_id=match.id, player_id=players[1])
    )
    await world.assert_armed_as_the_kernel_would(match.id)

    await world.move.execute(
        MoveMatchStartCommand(
            match_id=match.id, start=instant(START + timedelta(days=1))
        )
    )
    await world.assert_armed_as_the_kernel_would(match.id)

    await world.leave(match.id, players[0])
    await world.assert_armed_as_the_kernel_would(match.id)


async def test_a_third_payment_moves_the_schedule_with_no_deadline_moving(world):
    """T-12h becomes T-4h because a seat was paid for.

    This is the whole argument for *recomputed on every write*. Nothing about
    this match's calendar changed — same start, same club, same window — and the
    moment it is due to be looked at moved by eight hours.
    """

    match = await a_match(world)
    # Inside the commitment deadline, so the tier's lapse is the soonest thing
    # ahead. Outside it, `commit` at T-24h is nearer and the tier is what the
    # wake *after* this one is about — true, and not what this test is asking.
    world.clock.set(START - timedelta(hours=20))
    await seated(world, match, 2)

    at_two, reason_two = await world.stored_schedule(match.id)
    assert reason_two == WakeReason.HOLD_LAPSE.value
    assert at_two.replace(tzinfo=timezone.utc) == START - timedelta(hours=12)

    await seated(world, match, 1)

    at_three, reason_three = await world.stored_schedule(match.id)
    assert reason_three == WakeReason.HOLD_LAPSE.value
    assert at_three.replace(tzinfo=timezone.utc) == START - timedelta(hours=4)


async def test_a_cancelled_match_stores_no_moment_at_all(world):
    """A terminal match has nothing left to look at, so it leaves the index."""

    match = await a_match(world)
    await seated(world, match, 2)
    assert (await world.stored_schedule(match.id))[0] is not None

    await world.cancel.execute(
        CancelMatchCommand(match_id=match.id, cause=CancellationCause.CLUB)
    )

    assert await world.stored_schedule(match.id) == (None, None)
    assert await world.schedule.due(now=instant(START), limit=10) == []


async def test_a_match_past_its_result_window_stores_no_moment_either(world):
    """Not terminal, and still finished with the clock — which is why the index's
    predicate is *there is a moment* rather than a copy of terminality."""

    match = await a_match(world)
    world.clock.set(START - timedelta(hours=20))
    await seated(world, match, 4)
    assert (await world.stored_schedule(match.id))[0] is not None

    # A save with nothing changed, on a clock past the last threshold. It is the
    # narrowest way to ask *does a write recompute*, because there is no delta
    # for the answer to be a side effect of.
    world.clock.set(START + timedelta(days=2, hours=2))
    await world.matches.save(await world.matches.get(match.id))

    assert await world.stored_schedule(match.id) == (None, None)


# --- the due query ----------------------------------------------------------


async def test_due_returns_what_has_arrived_and_nothing_that_has_not(world):
    match = await a_match(world)
    world.clock.set(START - timedelta(hours=20))
    await seated(world, match, 2)
    at_column, _ = await world.stored_schedule(match.id)
    lapse = instant(at_column.replace(tzinfo=timezone.utc))

    a_minute_early = instant(lapse - timedelta(minutes=1))
    assert await world.schedule.due(now=a_minute_early, limit=10) == []

    due = await world.schedule.due(now=lapse, limit=10)
    assert [wake.match_id for wake in due] == [match.id]
    assert due[0].reason is WakeReason.HOLD_LAPSE
    assert due[0].scheduled_for == lapse


async def test_a_late_wake_is_still_due(world):
    """`next_wake_at <= now` stays true through a restart, a crash and a
    redeploy — which is the whole of ADR-0076's *"a restart loses nothing"*."""

    match = await a_match(world)
    await seated(world, match, 2)

    due = await world.schedule.due(now=instant(START + timedelta(days=30)), limit=10)

    assert [wake.match_id for wake in due] == [match.id]


async def test_due_is_ordered_soonest_first(world):
    soon = await a_match(world)
    later = await a_match(world, start=instant(START + timedelta(days=3)))
    await seated(world, soon, 2)
    await seated(world, later, 2)

    due = await world.schedule.due(
        now=instant(START + timedelta(days=30)), limit=10
    )

    assert [wake.match_id for wake in due] == [soon.id, later.id]


async def test_the_limit_takes_the_soonest_and_leaves_the_rest_due(world):
    soon = await a_match(world)
    later = await a_match(world, start=instant(START + timedelta(days=3)))
    await seated(world, soon, 2)
    await seated(world, later, 2)

    due = await world.schedule.due(now=instant(START + timedelta(days=30)), limit=1)

    assert [wake.match_id for wake in due] == [soon.id]


# --- re-arming --------------------------------------------------------------


async def test_re_arming_moves_the_moment_without_touching_the_version(world):
    """A schedule is derived, so moving it is not a change anybody could ask to
    have explained — and versioning it would make every look a write a player's
    own tap could lose a race to."""

    match = await a_match(world)
    before = (await world.matches.get(match.id)).version
    later = Boundary(WakeReason.PLAY, instant(START))

    armed = await world.schedule.re_arm(
        match_id=match.id, version=before, wake=later
    )

    assert armed
    at_column, reason = await world.stored_schedule(match.id)
    assert at_column.replace(tzinfo=timezone.utc) == START
    assert reason == WakeReason.PLAY.value
    assert (await world.matches.get(match.id)).version == before


async def test_re_arming_on_a_version_that_has_moved_writes_nothing(world):
    """Losing here is not an error and not a retry: a real writer moved the
    match, recomputed the schedule from the record it wrote, and its answer is
    the better one."""

    match = await a_match(world)
    stale = (await world.matches.get(match.id)).version
    await seated(world, match, 2)
    at_before, reason_before = await world.stored_schedule(match.id)

    armed = await world.schedule.re_arm(
        match_id=match.id,
        version=stale,
        wake=Boundary(WakeReason.PLAY, instant(START)),
    )

    assert not armed
    assert await world.stored_schedule(match.id) == (at_before, reason_before)


async def test_re_arming_to_nothing_takes_the_row_out_of_the_due_set(world):
    match = await a_match(world)
    version = (await world.matches.get(match.id)).version

    assert await world.schedule.re_arm(match_id=match.id, version=version, wake=None)

    assert await world.stored_schedule(match.id) == (None, None)
    assert await world.schedule.due(now=instant(START), limit=10) == []
