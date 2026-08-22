"""Claiming a seat through the real use cases, the real repository and a real look.

``test_seat_claims.py`` asserts the rules on the aggregate. This asserts the
three things that only exist once there is a database and a second match:

1. **One live claim per player is enforced across matches**, which no aggregate
   can see and which is therefore a port. Asserted both ways: a live claim
   elsewhere refuses her, and one that has run out does not — because *live* is
   composed and never waits on a reaper.
2. **A claim survives the round trip**, ends once, and its ended row stays.
3. **The expiry is genuinely reachable by the timekeeper**: the schedule column
   is armed at it, the tick finds the match due, and the look writes the
   receipt — with no branch on the reason it was handed.

Only the clock is in the test's hand. Everything else is the wiring a request
gets, from the composition root.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import (
    build_club_repository,
    build_court_holds,
    build_event_publisher,
    build_match_repository,
    build_match_schedule,
    build_reservation_repository,
    build_seat_claims,
    build_unit_of_work,
)
from app.kernel import SeatShare, Sport, filled, grosze, hours, instant, zloty
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
from app.modules.matches.application.commands import (
    ClaimSeatCommand,
    PostMatchCommand,
    RedeemSeatClaimCommand,
)
from app.modules.matches.application.post_match import PostMatch
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.application.seat_moves import ClaimSeat, RedeemSeatClaim
from app.modules.matches.application.take_match_wake import (
    MatchWakeBatch,
    TakeMatchWake,
)
from app.modules.matches.domain.errors import PlayerAlreadyClaiming
from app.modules.matches.infrastructure.sqlalchemy_match_models import (
    MatchORM,
    MatchSeatClaimORM,
)

START = instant(datetime(2026, 9, 8, 18, tzinfo=timezone.utc))
PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)

#: Days out, so nothing else on the match is within five minutes of anything.
TAPPED = START - timedelta(days=2)
FIVE_MINUTES = timedelta(minutes=5)


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
        schedule = build_match_schedule(session)
        claims = build_seat_claims(session)

        self.session = session
        self.clock = clock
        self.matches = matches
        self.claims = claims
        self.schedule = schedule
        self.register_club = RegisterClub(clubs, uow, clock)
        self.add_category = AddCourtCategory(clubs, uow, clock)
        self.add_court = AddCourt(clubs, uow, clock)
        self.post = PostMatch(matches, clubs, holds, uow, clock)
        self.claim = ClaimSeat(matches, holds, uow, clock, claims)
        self.redeem = RedeemSeatClaim(matches, holds, uow, clock)
        self.tick = MatchWakeBatch(
            schedule=schedule,
            look=TakeMatchWake(matches, schedule, holds, uow, clock),
            uow=uow,
            clock=clock,
        )

    async def claim_rows(self, match_id):
        rows = await self.session.execute(
            select(MatchSeatClaimORM)
            .where(MatchSeatClaimORM.match_id == match_id)
            .order_by(MatchSeatClaimORM.claimed_at, MatchSeatClaimORM.id)
        )
        return list(rows.scalars().all())

    async def claim_count(self) -> int:
        counted = select(func.count()).select_from(MatchSeatClaimORM)
        return (await self.session.execute(counted)).scalar_one()

    async def stored_schedule(self, match_id):
        row = (
            await self.session.execute(
                select(MatchORM.next_wake_at, MatchORM.wake_reason).where(
                    MatchORM.id == match_id
                )
            )
        ).one()
        return row.next_wake_at, row.wake_reason


@pytest.fixture
def clock():
    return _Clock(START - timedelta(days=14))


@pytest.fixture
async def world(session_factory, clock):
    async with session_factory() as session:
        yield _World(session, clock)


async def a_match(world, **overrides):
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
            policy=ClubPolicy(),
            payout=PAYOUT,
            pricing=ClubPricing(),
        )
    )
    category = await world.add_category.execute(
        AddCourtCategoryCommand(
            club_id=club.id,
            name=CategoryName("Padel · indoor"),
            sport=Sport.PADEL,
            rate=zloty(120),
        )
    )
    await world.add_court.execute(
        AddCourtCommand(
            club_id=club.id,
            category_id=category.id,
            label=CourtLabel("Court 1"),
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


# --- 1 · one live claim per player, across matches --------------------------


async def test_a_player_buying_a_seat_elsewhere_is_refused(world) -> None:
    """The half no aggregate can see. Two matches at two clubs; she taps in the
    first and then in the second, and the second refuses by name."""

    here, there = await a_match(world), await a_match(world)
    buyer = uuid4()
    world.clock.set(TAPPED)
    await world.claim.execute(ClaimSeatCommand(match_id=here.id, player_id=buyer))

    with pytest.raises(PlayerAlreadyClaiming):
        await world.claim.execute(
            ClaimSeatCommand(match_id=there.id, player_id=buyer)
        )

    assert await world.claim_count() == 1


async def test_a_claim_that_has_run_out_does_not_block_the_next_one(world) -> None:
    """**And no reaper has run.** *Live* is composed — unended **and** not yet
    expired — so a player is free the instant her five minutes are up, without
    waiting on a scheduled look. A unique index on the unended rows would have
    got this wrong, which is why there is not one."""

    here, there = await a_match(world), await a_match(world)
    buyer = uuid4()
    world.clock.set(TAPPED)
    await world.claim.execute(ClaimSeatCommand(match_id=here.id, player_id=buyer))

    world.clock.set(TAPPED + FIVE_MINUTES)
    await world.claim.execute(ClaimSeatCommand(match_id=there.id, player_id=buyer))

    assert await world.claim_count() == 2
    rows = await world.claim_rows(here.id)
    still_open = [row for row in rows if row.ended_at is None]
    assert still_open, "nothing reaped it, and it still did not block her"


async def test_a_claim_she_already_spent_does_not_block_the_next_one(world) -> None:
    """The **other** half of *live*, and the half an index cannot spell.

    The test above ends a claim by letting its clock run out; this one ends it
    by spending it, which leaves a row that is **ended with minutes still
    ahead of it**. A query that asked only the deadline would find that row and
    tell her she is still buying the seat she has already bought — locking her
    out of every other match for the rest of the five minutes she did not use.

    That is not hypothetical: it is exactly the predicate a mutation run found
    nothing else asserting.
    """

    here, there = await a_match(world), await a_match(world)
    buyer = uuid4()
    world.clock.set(TAPPED)
    await world.claim.execute(ClaimSeatCommand(match_id=here.id, player_id=buyer))
    await world.redeem.execute(
        RedeemSeatClaimCommand(match_id=here.id, player_id=buyer)
    )

    # One minute in: the spent claim's own deadline is still four minutes away.
    world.clock.set(TAPPED + timedelta(minutes=1))
    await world.claim.execute(ClaimSeatCommand(match_id=there.id, player_id=buyer))

    assert await world.claim_count() == 2
    spent = (await world.claim_rows(here.id))[0]
    assert spent.ended_at is not None
    assert spent.expires_at > spent.ended_at, "spent, and its deadline still ahead"


async def test_two_players_buying_in_one_match_are_both_allowed(world) -> None:
    match = await a_match(world)
    world.clock.set(TAPPED)

    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=uuid4()))
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=uuid4()))

    rows = await world.claim_rows(match.id)
    assert {row.seat_index for row in rows} == {0, 1}


# --- 2 · the round trip -----------------------------------------------------


async def test_a_claim_is_stored_whole_and_read_back(world) -> None:
    match = await a_match(world)
    buyer = uuid4()
    world.clock.set(TAPPED)

    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=buyer))

    reloaded = await world.matches.get(match.id)
    assert reloaded is not None
    [claim] = reloaded.claims
    assert claim.player_id == buyer
    assert claim.claimed_at == TAPPED
    assert claim.expires_at == TAPPED + FIVE_MINUTES
    assert claim.ended_at is None
    assert reloaded.live_claim_of(buyer, instant(TAPPED)) is not None


async def test_redeeming_stores_the_seat_paid_and_closes_the_claim(world) -> None:
    match = await a_match(world)
    buyer = uuid4()
    world.clock.set(TAPPED)
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=buyer))

    world.clock.set(TAPPED + timedelta(minutes=2))
    await world.redeem.execute(
        RedeemSeatClaimCommand(match_id=match.id, player_id=buyer)
    )

    reloaded = await world.matches.get(match.id)
    assert reloaded is not None
    assert filled(reloaded.as_record()) == 1
    [seat] = [one for one in reloaded.seats if one.player_id == buyer]
    assert seat.paid
    [row] = await world.claim_rows(match.id)
    # SQLite drops the offset it was handed; the stored instant is UTC.
    assert row.ended_at.replace(tzinfo=timezone.utc) == TAPPED + timedelta(minutes=2)


async def test_an_ended_claim_is_kept_rather_than_deleted(world) -> None:
    """The thirty seconds are measured from ``ended_at``, so a row that vanished
    would take the cooldown with it."""

    match = await a_match(world)
    world.clock.set(TAPPED)
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=uuid4()))

    world.clock.set(TAPPED + FIVE_MINUTES + timedelta(minutes=1))
    await world.tick.execute(worker_id="test")

    [row] = await world.claim_rows(match.id)
    assert row.ended_at is not None


# --- 3 · the expiry is a wake the timekeeper actually takes -----------------


async def test_the_schedule_is_armed_at_the_claim_s_expiry(world) -> None:
    """*"An expiry is a match wake, not a channel send"*, stored as a column.

    Days out, so nothing else on this match is within five minutes: the claim is
    unambiguously the next thing that happens to it whether she acts or not.
    """

    match = await a_match(world)
    world.clock.set(TAPPED)

    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=uuid4()))

    next_wake_at, reason = await world.stored_schedule(match.id)
    assert next_wake_at.replace(tzinfo=timezone.utc) == TAPPED + FIVE_MINUTES
    assert reason == "claimLapse"


async def test_the_tick_reaps_the_claim_and_re_arms_the_schedule(world) -> None:
    match = await a_match(world)
    buyer = uuid4()
    world.clock.set(TAPPED)
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=buyer))

    world.clock.set(TAPPED + FIVE_MINUTES)
    assert await world.tick.execute(worker_id="test") == 1

    reloaded = await world.matches.get(match.id)
    assert reloaded is not None
    assert reloaded.live_claim_of(buyer, instant(TAPPED + FIVE_MINUTES)) is None
    assert reloaded.unended_claims == []
    next_wake_at, reason = await world.stored_schedule(match.id)
    assert reason != "claimLapse", "the schedule moved on to the next threshold"
    assert next_wake_at is not None


async def test_a_second_tick_finds_nothing_left_to_reap(world) -> None:
    """A wake taken twice is looking twice: the second look re-derives from a
    record the first already moved, finds the claim ended, and writes nothing."""

    match = await a_match(world)
    world.clock.set(TAPPED)
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=uuid4()))

    world.clock.set(TAPPED + FIVE_MINUTES)
    await world.tick.execute(worker_id="test")
    before = (await world.matches.get(match.id)).version

    world.clock.set(TAPPED + FIVE_MINUTES + timedelta(seconds=1))
    await world.tick.execute(worker_id="test")

    assert (await world.matches.get(match.id)).version == before


async def test_the_reaped_seat_is_free_to_somebody_else_at_once(world) -> None:
    """The whole point of the five minutes ending: the race resumes, and the
    cascade's next question about that seat gets a different answer."""

    match = await a_match(world)
    dawdler = uuid4()
    world.clock.set(TAPPED)
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=dawdler))

    world.clock.set(TAPPED + FIVE_MINUTES)
    await world.tick.execute(worker_id="test")
    somebody_else = uuid4()
    await world.claim.execute(
        ClaimSeatCommand(match_id=match.id, player_id=somebody_else)
    )

    reloaded = await world.matches.get(match.id)
    assert reloaded is not None
    hers = reloaded.live_claim_of(somebody_else, instant(TAPPED + FIVE_MINUTES))
    assert hers is not None and hers.seat_index == 0
