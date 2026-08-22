"""A wake is a look, and taking one twice is looking twice.

ADR-0076 and `Raketa02/Raketa#72`. `test_match_schedule.py` asserts what is
stored; this asserts what happens when the stored moment arrives — over the real
Clubs, Courts and Matches contexts, with only the clock in the test's hand.

Three claims, and each fails differently:

1. **The handler re-derives, and never acts on the reason it was handed.** That
   reason was computed at a past write; the match may have moved since. Asserted
   twice over — behaviourally, by handing the same match every wrong reason in
   the enumeration and demanding one outcome, and structurally, by walking the
   timekeeper for a read of `wake.reason` at all. The behavioural half alone
   would pass a handler that read the reason and happened to branch the same way.
2. **A late wake produces what an on-time one would have.** It changes *when* we
   look and never *what we find*, which is what makes at-least-once scheduling
   affordable with no leader election and no distributed lock.
3. **A duplicate wake is a no-op** — no announcement, no version bump, no second
   court claimed. And it is a no-op *because* the first look moved the record,
   not because a table of handled keys said so: the record's own schedule column
   is the ledger of which wakes are outstanding.
"""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import (
    build_club_repository,
    build_match_wake_batch,
    build_court_holds,
    build_event_publisher,
    build_match_repository,
    build_match_schedule,
    build_reservation_repository,
    build_unit_of_work,
)
from app.bootstrap.events import build_event_delivery_worker, build_event_runtime
from app.core.config import Settings
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.kernel import (
    Outcome,
    SeatShare,
    Sport,
    WakeReason,
    grosze,
    hours,
    instant,
    keeping_a_court,
    live_outcome,
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
from app.modules.matches.application.commands import (
    DepartCommand,
    PaySeatCommand,
    PostMatchCommand,
    TakeSeatCommand,
)
from app.modules.matches.application.post_match import PostMatch
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.application.seat_moves import Depart, PaySeat, TakeSeat
from app.modules.matches.application.take_match_wake import (
    MatchWakeBatch,
    TakeMatchWake,
    WakeOutcome,
)
from app.modules.matches.domain.wake import MatchWake
from app.modules.matches.infrastructure.sqlalchemy_match_models import MatchORM

START = instant(datetime(2026, 9, 8, 18, tzinfo=timezone.utc))
PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)

#: Inside the commitment deadline, so the tier's lapse is the next thing ahead.
INSIDE_COMMITMENT = START - timedelta(hours=20)


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

        self.session = session
        self.clock = clock
        self.matches = matches
        self.reservations = reservations
        self.schedule = schedule
        self.look = TakeMatchWake(matches, schedule, holds, uow, clock)
        self.tick = MatchWakeBatch(
            schedule=schedule, look=self.look, uow=uow, clock=clock
        )
        self.register_club = RegisterClub(clubs, uow, clock)
        self.add_category = AddCourtCategory(clubs, uow, clock)
        self.add_court = AddCourt(clubs, uow, clock)
        self.post = PostMatch(matches, clubs, holds, uow, clock)
        self.take = TakeSeat(matches, holds, uow, clock)
        self.pay = PaySeat(matches, holds, uow, clock)
        self.depart = Depart(matches, holds, uow, clock)

    async def announcements(self) -> int:
        counted = select(func.count()).select_from(EventOutboxORM)
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

    async def the_one_due_wake(self, at) -> MatchWake:
        due = await self.schedule.due(now=instant(at), limit=10)
        assert len(due) == 1, f"expected one due wake, got {len(due)}"
        return due[0]


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


async def a_match_holding_a_court(world, **overrides):
    """Two paid seats inside the commitment deadline: a court kept aside, and a
    tier that lapses twelve hours before play."""

    match = await a_match(world, **overrides)
    world.clock.set(INSIDE_COMMITMENT)
    for _ in range(2):
        player = uuid4()
        await world.take.execute(
            TakeSeatCommand(match_id=match.id, player_id=player)
        )
        await world.pay.execute(PaySeatCommand(match_id=match.id, player_id=player))
    assert keeping_a_court((await world.matches.get(match.id)).as_record())
    return match


async def a_committed_match_that_lost_somebody(world, **overrides):
    """Four paid seats past the deadline, then one player out — a leaver whose
    money nothing has decided and a hole nobody has filled."""

    match = await a_match(world, **overrides)
    world.clock.set(INSIDE_COMMITMENT)
    players = [uuid4() for _ in range(4)]
    for player in players:
        await world.take.execute(
            TakeSeatCommand(match_id=match.id, player_id=player)
        )
        await world.pay.execute(PaySeatCommand(match_id=match.id, player_id=player))

    stored = await world.matches.get(match.id)
    assert stored is not None and stored.committed_at is not None
    await world.depart.execute(
        DepartCommand(
            match_id=match.id,
            player_id=players[0],
            quote=live_outcome(stored.as_record(), instant(world.clock.now())),
        )
    )
    return match, players[0]


async def the_departure(world, match_id, player_id):
    stored = await world.matches.get(match_id)
    assert stored is not None
    departure = stored.departure_of(player_id)
    assert departure is not None
    return departure


# --- 1. the look re-derives -------------------------------------------------


async def test_a_wake_at_the_tier_gives_the_court_back(world):
    match = await a_match_holding_a_court(world)
    wake = await world.the_one_due_wake(START - timedelta(hours=12))
    assert wake.reason is WakeReason.HOLD_LAPSE

    world.clock.set(START - timedelta(hours=12))
    outcome = await world.look.execute(wake)

    assert outcome is WakeOutcome.ACTED
    stored = await world.matches.get(match.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())
    assert await world.reservations.for_match(match.id) is None


@pytest.mark.parametrize("reason", list(WakeReason), ids=lambda r: r.value)
async def test_the_reason_it_was_handed_changes_nothing(world, reason):
    """Every one of the eleven names, over the same record and the same clock.

    A handler that read the reason would have to answer *release the court* to
    `holdLapse` and something else to `play` — so eleven identical outcomes is
    the behavioural half of *nothing branches on it*.
    """

    match = await a_match_holding_a_court(world)
    world.clock.set(START - timedelta(hours=12))

    outcome = await world.look.execute(
        MatchWake(
            match_id=match.id,
            reason=reason,
            scheduled_for=instant(START - timedelta(hours=12)),
        )
    )

    assert outcome is WakeOutcome.ACTED
    stored = await world.matches.get(match.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())


async def test_a_look_that_finds_nothing_writes_no_fact_and_still_moves_on(world):
    """The re-arm is what stops the tick picking the row up again next second.

    Without it a look that stands leaves `next_wake_at` in the past for ever, and
    the timekeeper spins on one match at one query per tick.
    """

    match = await a_match_holding_a_court(world)
    wake = await world.the_one_due_wake(START - timedelta(hours=12))
    # A minute early: the tier has not lapsed, so the ladder has nothing to do.
    world.clock.set(START - timedelta(hours=12, minutes=1))
    version = (await world.matches.get(match.id)).version
    announced = await world.announcements()

    outcome = await world.look.execute(wake)

    assert outcome is WakeOutcome.NOTHING_TO_DO
    assert (await world.matches.get(match.id)).version == version
    assert await world.announcements() == announced
    at_column, reason = await world.stored_schedule(match.id)
    assert at_column.replace(tzinfo=timezone.utc) == START - timedelta(hours=12)
    assert reason == WakeReason.HOLD_LAPSE.value


async def test_a_wake_for_a_match_that_is_gone_is_not_an_error(world):
    outcome = await world.look.execute(
        MatchWake(
            match_id=uuid4(),
            reason=WakeReason.PLAY,
            scheduled_for=instant(START),
        )
    )

    assert outcome is WakeOutcome.GONE


# --- 2. lateness ------------------------------------------------------------


async def test_a_late_wake_finds_what_an_on_time_one_would_have(world):
    """Three days late, and the same court goes back."""

    match = await a_match_holding_a_court(world)
    wake = await world.the_one_due_wake(START - timedelta(hours=12))

    world.clock.set(START + timedelta(days=3))
    outcome = await world.look.execute(wake)

    assert outcome is WakeOutcome.ACTED
    stored = await world.matches.get(match.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())
    assert await world.reservations.for_match(match.id) is None


async def test_a_wake_taken_after_the_record_moved_acts_on_the_record(world):
    """The reason said *the far tier lapses*; by the time we looked, a third seat
    had been paid and the near tier had not. A handler acting on the reason takes
    the court off a match that has more claim to it than when it was scheduled."""

    match = await a_match_holding_a_court(world)
    wake = await world.the_one_due_wake(START - timedelta(hours=12))
    assert wake.reason is WakeReason.HOLD_LAPSE

    player = uuid4()
    await world.take.execute(TakeSeatCommand(match_id=match.id, player_id=player))
    await world.pay.execute(PaySeatCommand(match_id=match.id, player_id=player))

    world.clock.set(START - timedelta(hours=12))
    outcome = await world.look.execute(wake)

    assert outcome is WakeOutcome.NOTHING_TO_DO
    stored = await world.matches.get(match.id)
    assert stored is not None
    assert keeping_a_court(stored.as_record())
    assert await world.reservations.for_match(match.id) is not None


# --- 3. a duplicate is a no-op ----------------------------------------------


async def test_taking_the_same_wake_twice_writes_nothing_the_second_time(world):
    """The key is `{matchId}:{threshold}:{scheduledFor}` and it is not looked up
    anywhere — safety comes from the second look finding a moved record."""

    match = await a_match_holding_a_court(world)
    wake = await world.the_one_due_wake(START - timedelta(hours=12))
    world.clock.set(START - timedelta(hours=12))

    assert await world.look.execute(wake) is WakeOutcome.ACTED
    version = (await world.matches.get(match.id)).version
    announced = await world.announcements()
    schedule = await world.stored_schedule(match.id)

    assert await world.look.execute(wake) is WakeOutcome.NOTHING_TO_DO

    assert (await world.matches.get(match.id)).version == version
    assert await world.announcements() == announced
    assert await world.stored_schedule(match.id) == schedule


async def test_the_idempotency_key_is_the_three_facts_adr_0076_names(world):
    match = await a_match_holding_a_court(world)
    wake = await world.the_one_due_wake(START - timedelta(hours=12))

    assert wake.key == (
        f"{match.id}:holdLapse:{(START - timedelta(hours=12)).isoformat()}"
    )


async def test_two_wakes_for_one_match_are_two_different_keys(world):
    await a_match_holding_a_court(world)
    first = await world.the_one_due_wake(START - timedelta(hours=12))
    world.clock.set(START - timedelta(hours=12))
    await world.look.execute(first)

    second = await world.the_one_due_wake(START + timedelta(days=3))

    assert second.key != first.key


# --- the tick ---------------------------------------------------------------


async def test_the_tick_takes_every_due_match(world):
    """Two clubs, two matches, one query — and both courts go back."""

    first = await a_match_holding_a_court(world)
    second = await a_match_holding_a_court(world)

    world.clock.set(START - timedelta(hours=12))
    taken = await world.tick.execute(worker_id="test")

    assert taken == 2
    for match in (first, second):
        stored = await world.matches.get(match.id)
        assert stored is not None
        assert not keeping_a_court(stored.as_record())


async def test_the_tick_leaves_a_match_whose_moment_has_not_arrived(world):
    await a_match_holding_a_court(world)

    world.clock.set(START - timedelta(hours=13))
    assert await world.tick.execute(worker_id="test") == 0


async def test_the_tick_empties_the_due_set_it_ran_over(world):
    """The point of the re-arm, at the level the worker sees it: a second tick a
    moment later finds nothing, rather than the same match again."""

    await a_match_holding_a_court(world)
    world.clock.set(START - timedelta(hours=12))

    assert await world.tick.execute(worker_id="test") == 1
    assert await world.tick.execute(worker_id="test") == 0


async def test_one_failing_look_does_not_stop_the_rest_of_the_tick(world):
    """The matches in a tick are unrelated, so one in a bad state must not stop
    every court in the country being given back."""

    healthy = await a_match_holding_a_court(world)
    broken = await a_match_holding_a_court(world)
    world.clock.set(START - timedelta(hours=12))

    real = world.look.execute

    async def _explode(wake):
        if wake.match_id == broken.id:
            raise RuntimeError("this match is having a bad day")
        return await real(wake)

    world.look.execute = _explode  # type: ignore[method-assign]

    taken = await world.tick.execute(worker_id="test")

    assert taken == 1
    stored = await world.matches.get(healthy.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())


# --- the structural halves --------------------------------------------------

_TIMEKEEPER = (
    Path(__file__).resolve().parents[2]
    / "app/modules/matches/application/take_match_wake.py"
)


def test_the_handler_never_reads_the_reason_it_was_handed():
    """The structural half of claim 1.

    The behavioural half above would pass a handler that read `wake.reason` and
    happened to branch the same way for all eleven; and it would keep passing
    while somebody added a twelfth that branched differently. This is an AST walk
    for the attribute access itself.
    """

    tree = ast.parse(_TIMEKEEPER.read_text())
    read = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr == "reason"
        and isinstance(node.value, ast.Name)
        and node.value.id == "wake"
    ]

    assert not read, "the timekeeper reads the reason it was handed"


def test_the_walk_can_tell_the_difference():
    """The negative control, because a guard nobody has seen fire is one nobody
    should watch."""

    tree = ast.parse(
        "async def execute(self, wake):\n"
        "    if wake.reason is WakeReason.HOLD_LAPSE:\n"
        "        return None\n"
    )
    read = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr == "reason"
        and isinstance(node.value, ast.Name)
        and node.value.id == "wake"
    ]

    assert read


# --- the wiring -------------------------------------------------------------


async def test_a_wake_at_the_start_settles_a_leaver_nobody_replaced(world):
    """The timekeeper's **second actor**, and the reason a leaver's card ever
    stops saying *not yet decided*.

    Nothing else in the system would ever settle her: no filler arrived, so no
    seat event touched her departure, and the match was not cancelled. Without
    this look her money stays open for ever on a match that has been played.
    """

    match, leaver = await a_committed_match_that_lost_somebody(world)
    assert not (await the_departure(world, match.id, leaver)).is_settled

    world.clock.set(START)
    wake = await world.the_one_due_wake(START)
    outcome = await world.look.execute(wake)

    assert outcome is WakeOutcome.ACTED
    settled = await the_departure(world, match.id, leaver)
    assert settled.outcome is Outcome.FORFEITED
    assert settled.settled_at == instant(START)


async def test_a_wake_before_the_start_leaves_her_money_open(world):
    """Every earlier wake belongs to the other actor, or to nobody.

    A committed match one seat short wakes next when the rescue window opens,
    and a filler could still arrive from there — so settling her then would take
    money off somebody whose seat was about to sell.
    """

    match, leaver = await a_committed_match_that_lost_somebody(world)
    rescue = START - timedelta(hours=4)
    wake = await world.the_one_due_wake(rescue)
    assert wake.reason is WakeReason.RESCUE

    world.clock.set(rescue)
    await world.look.execute(wake)

    assert not (await the_departure(world, match.id, leaver)).is_settled


async def test_settling_her_is_taken_twice_without_moving_anything(world):
    """A duplicate look is looking twice: the second re-derives, finds her
    already settled, and writes nothing."""

    match, leaver = await a_committed_match_that_lost_somebody(world)
    world.clock.set(START)
    wake = await world.the_one_due_wake(START)
    await world.look.execute(wake)
    settled_at = (await the_departure(world, match.id, leaver)).settled_at
    before = await world.announcements()
    version = (await world.matches.get(match.id)).version

    world.clock.set(START + timedelta(minutes=1))
    outcome = await world.look.execute(wake)

    assert outcome is not WakeOutcome.ACTED
    assert (await the_departure(world, match.id, leaver)).settled_at == settled_at
    assert await world.announcements() == before
    assert (await world.matches.get(match.id)).version == version


async def test_the_composed_timekeeper_gives_a_court_back(world):
    """The tick as the process actually builds it, over the real Courts context.

    Everything above constructs the use case by hand, which proves the use case
    and not the wiring. `build_match_wake_batch` is the only thing between a
    running API and a court that never goes back on sale, and nothing else runs
    it — a factory whose object nobody exercises proves that a constructor
    accepts its arguments.
    """

    match = await a_match_holding_a_court(world)
    world.clock.set(START - timedelta(hours=12))

    composed = build_match_wake_batch(
        session=world.session,
        event_runtime=build_event_runtime(),
        clock=world.clock,
    )
    taken = await composed.execute(worker_id="composed")

    assert taken == 1
    stored = await world.matches.get(match.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())
    assert await world.reservations.for_match(match.id) is None


def test_the_worker_the_process_starts_carries_a_timekeeper():
    """ADR-0076's *"the existing `EventWorker` gains …"*, asserted on the object
    the lifespan starts rather than on the ability to pass one in."""

    worker = build_event_delivery_worker(
        event_runtime=build_event_runtime(),
        session_factory=None,  # type: ignore[arg-type]
        settings=Settings(WRITER_DB_URL="sqlite+aiosqlite:///:memory:"),
    )

    assert worker._wake_batch_factory is not None
