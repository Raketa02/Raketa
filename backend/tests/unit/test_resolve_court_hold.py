"""The hold ladder acting: a court claimed, a court given back, and one refused.

`tests/unit/test_hold_ladder.py` asserts what the ladder *says*. This asserts
what it *does* — over the real Courts context, the real Matches repository and a
real (SQLite) session, with only the clock in the test's hand. Three claims:

1. **Entering a tier and being given a court are one transaction.** There is no
   instant at which a stored record is in the combination the kernel refuses —
   which matters because that combination arrives as a five-hundred on somebody's
   home screen rather than as a red test.
2. **A grant that finds no court is an inventory loss.** `keep_aside` answers
   *nothing was free* and never *somebody was faster* (ADR-0035), so the club has
   no court of that category for that hour and the match cannot be played.
3. **The court a match holds is a reservation, and giving it back is a release.**
   The match stores no `reservation_id` — the reservation already says
   `MatchHeld(match_id)`.
"""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from app.bootstrap.composition import (
    build_club_repository,
    build_court_holds,
    build_event_publisher,
    build_match_repository,
    build_reservation_repository,
    build_unit_of_work,
)
from app.kernel import (
    HoldMove,
    MatchKind,
    SeatShare,
    Situation,
    Sport,
    grosze,
    hours,
    instant,
    keeping_a_court,
    live_outcome,
    minutes,
    situation,
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
from app.modules.courts.domain.reservation import HolderKind, MatchHeld
from app.modules.matches.application.cancel_match import CancelMatch
from app.modules.matches.application.commands import (
    CancellationCause,
    CancelMatchCommand,
    MoveMatchStartCommand,
    PaySeatCommand,
    PostMatchCommand,
    ResolveCourtHoldCommand,
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
    """Clubs, Courts and Matches over one session, with the ladder between them."""

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

        self.clock = clock
        self.matches = matches
        self.reservations = reservations
        self.holds = holds
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


@pytest.fixture
def clock():
    return _Clock(START - timedelta(days=14))


@pytest.fixture
async def world(session_factory, clock):
    async with session_factory() as session:
        yield _World(session, clock)


async def a_club(world, *, courts: int = 2, policy=None):
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
    return club, category


async def a_match(world, *, courts: int = 2, policy=None, **overrides):
    club, category = await a_club(world, courts=courts, policy=policy)
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
    """`count` players on the match, `paid` of them having paid. Returns them."""

    players = [uuid4() for _ in range(count)]
    for player in players:
        await world.take.execute(
            TakeSeatCommand(match_id=match.id, player_id=player)
        )
    for player in players[: count if paid is None else paid]:
        await world.pay.execute(PaySeatCommand(match_id=match.id, player_id=player))
    return players


# --- 1. entering a tier and getting a court are one transaction -------------


async def test_a_second_payment_earns_a_court_in_the_write_that_earns_it(world):
    match = await a_match(world)

    await seated(world, match, 2)

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert keeping_a_court(stored.as_record())
    assert stored.held_since == instant(world.clock.now())

    reservation = await world.reservations.for_match(match.id)
    assert reservation is not None
    assert reservation.holder == MatchHeld(match_id=match.id)
    assert reservation.kind is HolderKind.MATCH
    assert reservation.played.start == START


async def test_one_paid_seat_earns_nothing(world):
    match = await a_match(world)

    await seated(world, match, 1)

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())
    assert await world.reservations.for_match(match.id) is None


async def test_a_club_that_never_holds_speculatively_is_granted_no_court(world):
    """AC: `maxHoldAge = 0` never receives a speculative hold, end to end."""

    match = await a_match(world, policy=ClubPolicy(max_hold_age=minutes(0)))

    await seated(world, match, 2)

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert stored.held_since is None
    assert await world.reservations.for_match(match.id) is None


async def test_a_capped_club_does_not_make_the_record_unreadable(world):
    """The combination the kernel refuses is never stored, because it is never
    left behind: the tier is entered and the hold granted in one write."""

    match = await a_match(world, policy=ClubPolicy(max_hold_age=hours(48)))

    await seated(world, match, 2)

    stored = await world.matches.get(match.id)
    assert stored is not None
    # Would raise `InvariantViolated` on a record whose tier was entered without
    # a hold — which is the whole reason the ladder runs inside the write. What
    # it answers instead is the card that says a court is being kept aside.
    assert situation(stored.as_record(), None, instant(world.clock.now())) is (
        Situation.HELD_SOFT
    )


async def test_taking_a_seat_earns_nothing_because_holding_is_not_paying(world):
    match = await a_match(world)

    await seated(world, match, 4, paid=0)

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())


# --- 2. a grant with nothing free is an inventory loss ----------------------


async def test_a_match_that_can_get_no_court_loses_its_inventory(world):
    """*Nothing was free* — the single story ADR-0035 promises the player."""

    match = await a_match(world, courts=0)

    await seated(world, match, 2)

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert stored.inventory_lost
    assert stored.held_since is None
    assert situation(stored.as_record(), None, instant(world.clock.now())) is (
        Situation.INVENTORY_LOST
    )


async def test_the_last_free_court_goes_to_one_of_two_matches_and_the_other_loses_it(
    world,
):
    """Losing inventory is a **query result**, never a race outcome."""

    club, category = await a_club(world, courts=1)
    posted = [
        await world.post.execute(
            PostMatchCommand(
                club_id=club.id,
                category_id=category.id,
                sport=Sport.PADEL,
                start=START,
                duration=hours(1),
                share=SeatShare(grosze(3800)),
            )
        )
        for _ in range(2)
    ]

    for match in posted:
        await seated(world, match, 2)

    stored = [await world.matches.get(match.id) for match in posted]
    assert [one for one in stored if one is not None and one.held_since] != []
    assert [one for one in stored if one is not None and one.inventory_lost] != []


# --- 3. giving the court back -----------------------------------------------


async def test_a_departure_that_leaves_the_tier_gives_the_court_back(world):
    match = await a_match(world)
    players = await seated(world, match, 2)

    await world.leave(match.id, players[0])

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())
    assert stored.released_at == instant(world.clock.now())
    assert await world.reservations.for_match(match.id) is None


async def test_the_released_reservation_keeps_its_row(world):
    """Released, never deleted — a court's history is a query over reservations."""

    match = await a_match(world)
    players = await seated(world, match, 2)
    reservation = await world.reservations.for_match(match.id)
    assert reservation is not None

    await world.leave(match.id, players[0])

    history = await world.reservations.for_court(reservation.court_id)
    assert [one.id for one in history] == [reservation.id]
    assert not history[0].is_live


async def test_a_cancelled_match_gives_its_court_back(world):
    match = await a_match(world)
    await seated(world, match, 2)
    assert await world.reservations.for_match(match.id) is not None

    await world.cancel.execute(
        CancelMatchCommand(match_id=match.id, cause=CancellationCause.CLUB)
    )

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())
    assert await world.reservations.for_match(match.id) is None


async def test_a_court_given_back_can_be_taken_again(world):
    """Staleness is never latched, so a card may go *back* from released to held."""

    match = await a_match(world)
    players = await seated(world, match, 2)
    await world.leave(match.id, players[0])

    await seated(world, match, 1)

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert keeping_a_court(stored.as_record())
    assert await world.reservations.for_match(match.id) is not None


async def test_moving_the_hour_past_the_tier_gives_the_court_back(world):
    """Every deadline is relative to `start`, so moving it moves the tier's lapse."""

    match = await a_match(world)
    await seated(world, match, 2)

    world.clock.set(START - timedelta(hours=13))
    await world.move.execute(
        MoveMatchStartCommand(
            match_id=match.id, start=instant(START - timedelta(hours=1))
        )
    )

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())


# --- the wake's own entry point ---------------------------------------------


async def test_a_look_with_nothing_to_do_writes_nothing(world):
    match = await a_match(world)
    await seated(world, match, 2)
    before = (await world.matches.get(match.id)).version

    resolved = await world.holds.execute(ResolveCourtHoldCommand(match_id=match.id))

    assert resolved.held_since is not None
    assert resolved.version == before


async def test_a_look_after_the_tier_lapsed_takes_the_court_back(world):
    """A wake is a **look**: nothing is passed in about why, and the answer comes
    from the record and the clock."""

    match = await a_match(world)
    await seated(world, match, 2)
    assert await world.reservations.for_match(match.id) is not None

    world.clock.set(START - timedelta(hours=11))
    await world.holds.execute(ResolveCourtHoldCommand(match_id=match.id))

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert not keeping_a_court(stored.as_record())
    assert await world.reservations.for_match(match.id) is None


async def test_a_late_look_finds_what_an_on_time_one_would_have(world):
    """A late wake changes *when* we look and never *what we find*."""

    match = await a_match(world)
    await seated(world, match, 2)

    world.clock.set(START - timedelta(minutes=90))
    move = await world.holds.apply(
        await world.matches.get(match.id), at=instant(world.clock.now())
    )

    assert move is HoldMove.WITHDRAW


async def test_a_private_court_is_claimed_the_moment_it_is_posted(world):
    """A private court belongs to whoever bought it, from its first instant."""

    match = await a_match(world, kind=MatchKind.PRIVATE)

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert keeping_a_court(stored.as_record())
    assert await world.reservations.for_match(match.id) is not None


# --- the obligation itself --------------------------------------------------

_APPLICATION = Path(__file__).resolve().parents[2] / "app/modules/matches/application"

#: The one module allowed to save a match without asking the ladder first: it
#: *is* the ladder, and `apply` is what it calls.
_THE_LADDER = "resolve_court_hold.py"

#: The result route is `Raketa02/Raketa#79` and writes only a score. It is listed
#: by name rather than inferred, so a module that stops being about results has
#: to be re-argued here rather than silently keeping its exemption.
_WRITES_NO_COURT_FACT = {"record_result.py"}


def _persisting_functions(tree: ast.AST):
    """Every function that calls `self._matches.save` or `.add`, with its body."""

    for node in ast.walk(tree):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        calls = [
            call
            for call in ast.walk(node)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr in {"save", "add"}
            and isinstance(call.func.value, ast.Attribute)
            and call.func.value.attr == "_matches"
        ]
        if calls:
            yield node


def test_every_matches_write_asks_the_ladder_before_it_saves():
    """The obligation, enforced structurally because nothing else can enforce it.

    Two facts have to stay in step and the ladder is the only thing allowed to
    move them; a write that saves without asking leaves a record the kernel
    refuses to read, and nothing about a green suite would look different. So
    this walks the package rather than trusting the next person to remember.
    """

    unchecked = []
    for module in sorted(_APPLICATION.glob("*.py")):
        if module.name in {_THE_LADDER} | _WRITES_NO_COURT_FACT:
            continue
        tree = ast.parse(module.read_text())
        for function in _persisting_functions(tree):
            asked = any(
                isinstance(call.func, ast.Attribute)
                and call.func.attr == "apply"
                and isinstance(call.func.value, ast.Attribute)
                and call.func.value.attr == "_holds"
                for call in ast.walk(function)
                if isinstance(call, ast.Call)
            )
            if not asked:
                unchecked.append(f"{module.name}::{function.name}")

    assert not unchecked, f"a match is saved without asking the ladder: {unchecked}"


def test_the_walk_can_tell_the_difference():
    """The negative control: a persisting function that does not ask is found.

    A guard nobody has seen fire is one nobody should watch — and this one is a
    glob over a directory, which is the shape that passes silently when it stops
    matching anything.
    """

    source = """
class Writer:
    async def execute(self, command):
        match = await self._matches.get(command.match_id)
        stored = await self._matches.save(match)
        return stored
"""
    tree = ast.parse(source)
    functions = list(_persisting_functions(tree))

    assert [one.name for one in functions] == ["execute"]
    assert not any(
        isinstance(call.func, ast.Attribute) and call.func.attr == "apply"
        for function in functions
        for call in ast.walk(function)
        if isinstance(call, ast.Call)
    )


def test_the_walk_looks_at_the_modules_that_exist():
    """A glob matching nothing passes, so the count is asserted rather than trusted."""

    assert len(list(_APPLICATION.glob("*.py"))) >= 7
