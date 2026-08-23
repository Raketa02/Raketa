"""The seat payment that earns a court, over four real contexts and one session.

``Raketa02/Raketa#70``. Clubs, Courts, Matches and Money are all real here —
real aggregates, real repositories, the real hold ladder, a real event store and
a real (SQLite) session — with only the clock in the test's hand. A fake
anywhere in that chain would leave the one thing this ticket is about tested by
nothing: **the transaction**.

Five claims, and each fails differently.

1. **The seat, the reservation and both outbox rows are one write.** ADR-0035:
   *"a seat payment that earns a court, and the court it earns, are one event or
   they are a bug."*
2. **A failure anywhere inside it leaves none of the four rows behind.** Asserted
   by breaking each of the four collaborators in turn — which is the only way to
   see a transaction boundary at all, because a boundary that holds and a
   boundary that does not are the same green suite until something fails. Three
   of the four rows are asserted **here**; the reservation is
   ``tests/integration/test_seat_payment_transaction.py``, and the reason is in
   that case's own docstring — it is a genuine SQLite limitation and not a
   choice.
3. **A grant that finds no court records an inventory loss, and the money still
   lands.** Losing inventory is a query result and never a race (ADR-0035), so
   it is a fact the write records rather than an error the payment fails on.
4. **The two custody regimes are two different chains.** The same 38 zł is held
   on one path and gone on the other, and the difference is invisible on the
   screen (ADR-0056).
5. **The seam between the two transactions is safe in one direction.** A payment
   for a seat that has gone is recorded and given back in one append; a payment
   for a seat that is already hers is recorded rather than refunded, which is
   what heals a process that died between the two.
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
    build_domain_event_store,
    build_event_publisher,
    build_ledger_repository,
    build_match_repository,
    build_reservation_repository,
    build_seats,
    build_unit_of_work,
)
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.kernel import (
    Grosze,
    InvariantViolated,
    MatchKind,
    PayModel,
    SeatShare,
    Sport,
    grosze,
    hours,
    instant,
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
    ClaimSeatCommand,
    PostMatchCommand,
    TakeSeatCommand,
)
from app.modules.matches.application.post_match import PostMatch
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.application.seat_moves import ClaimSeat, TakeSeat
from app.modules.matches.domain.errors import MatchNotFound
from app.modules.money.application.commands import (
    AcrossTheCounter,
    Online,
    PayForASeatCommand,
)
from app.modules.money.application.pay_for_a_seat import PayForASeat
from app.modules.money.application.record_movements import RecordMovements
from app.modules.money.application.record_share import RecordShare
from app.modules.money.domain.causes import MovementCause
from app.modules.money.domain.errors import (
    CounterShareNotOwed,
    DuplicateMovementReference,
    PaymentNamesNoSeat,
)
from app.modules.money.domain.invariants import breaches_in, every_seat_chain_closes
from app.modules.money.domain.movement import SeatRef
from app.modules.money.domain.parties import ClubParty, PlayerParty, RaketaParty
from app.modules.money.domain.reference import Reference, ReferenceKind

START = instant(datetime(2026, 9, 8, 18, tzinfo=timezone.utc))
SHARE = SeatShare(grosze(3800))
PAYOUT = PayoutDestination(
    account_holder="Zabłocie Sport", iban="PL61109010140000071219812874"
)


def pay(token: str) -> Reference:
    return Reference(ReferenceKind.PAYMENT, token)


class _Clock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now = self._now + delta


class _CountingUnitOfWork:
    """The real unit of work, with its commits counted.

    The count is the only externally visible thing that says *one transaction*
    rather than *two writes that both happened*: the four rows are one commit,
    the movement is the second, and a third would mean somebody split the write
    the ticket exists to keep together.
    """

    def __init__(self, inner) -> None:
        self._inner = inner
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1
        await self._inner.commit()

    async def flush(self) -> None:
        await self._inner.flush()

    async def rollback(self) -> None:
        await self._inner.rollback()


class _World:
    """Clubs, Courts, Matches and Money over one session."""

    def __init__(self, session, clock) -> None:
        self.session = session
        self.clock = clock

        clubs = build_club_repository(session)
        self.events = build_event_publisher(session)
        self.reservations = build_reservation_repository(session)
        self.matches = build_match_repository(session, events=self.events, clock=clock)
        self.uow = _CountingUnitOfWork(build_unit_of_work(session))

        self.holds = ResolveCourtHold(
            self.matches,
            build_court_holds(
                ClaimCourt(clubs, self.reservations, self.uow), self.reservations
            ),
            self.uow,
            clock,
        )
        self.ledgers = build_ledger_repository(
            event_store=build_domain_event_store(session), events=self.events
        )
        movements = RecordMovements(self.ledgers, self.uow, clock)
        self.seats = build_seats(
            matches=self.matches, holds=self.holds, reservations=self.reservations
        )
        self.pay_for_a_seat = PayForASeat(
            self.seats, RecordShare(movements), movements, self.uow, clock
        )

        self.register_club = RegisterClub(clubs, self.uow, clock)
        self.add_category = AddCourtCategory(clubs, self.uow, clock)
        self.add_court = AddCourt(clubs, self.uow, clock)
        self.post = PostMatch(self.matches, clubs, self.holds, self.uow, clock)
        self.take = TakeSeat(self.matches, self.holds, self.uow, clock)
        self.claim = ClaimSeat(
            self.matches, self.holds, self.uow, clock, _AnybodyMayClaim()
        )

    async def outbox(self, *names: str) -> list[str]:
        """Which of these announcements are on the outbox right now.

        Read off the **stored** rows rather than off a recording publisher: the
        claim is that they are in the transaction, and a list a fake collected
        in memory would say nothing about whether anything reached disk.
        """

        rows = await self.session.execute(
            select(EventOutboxORM.event_type).order_by(EventOutboxORM.created_at)
        )
        return [name for (name,) in rows if name in names]


class _AnybodyMayClaim:
    """The cross-match *is she already buying a seat somewhere else* read.

    Answers *no* always. These cases are about the payment, and the one live
    claim per player rule has its own suite — a real adapter here would make
    every fixture depend on a question none of them is asking.
    """

    async def live_for(self, player_id, *, at):
        return None


@pytest.fixture
def clock():
    return _Clock(START - timedelta(days=14))


@pytest.fixture
async def world(session_factory, clock):
    async with session_factory() as session:
        yield _World(session, clock)


async def a_club(world, *, courts: int = 2):
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
    for index in range(courts):
        await world.add_court.execute(
            AddCourtCommand(
                club_id=club.id,
                category_id=category.id,
                label=CourtLabel(f"Court {index + 1}"),
            )
        )
    return club, category


async def a_match(world, *, courts: int = 2, club=None, category=None, **overrides):
    if club is None:
        club, category = await a_club(world, courts=courts)
    facts = dict(
        club_id=club.id,
        category_id=category.id,
        sport=Sport.PADEL,
        start=START,
        duration=hours(1),
        share=SHARE,
    )
    facts.update(overrides)
    return club, category, await world.post.execute(PostMatchCommand(**facts))


async def paid_by_claiming(world, match, player, *, token: str, amount=None):
    """The ordinary online path: she claims a seat, then the money lands."""

    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=player))
    return await world.pay_for_a_seat.execute(
        PayForASeatCommand(
            match_id=match.id,
            player_id=player,
            amount=amount or Grosze(int(SHARE)),
            reference=pay(token),
            channel=Online(settlement=pay(f"{token}s")),
        )
    )


# ---------------------------------------------------------------------------
# 1. The seat, the reservation and both outbox rows are one write
# ---------------------------------------------------------------------------


async def test_a_seat_payment_that_earns_a_court_writes_all_four_rows(world):
    """The second paid seat crosses a hold tier, so this payment earns the court.

    Four rows: the seat, the reservation, and the outbox rows for both.
    """

    _, _, match = await a_match(world)
    first, second = uuid4(), uuid4()
    await paid_by_claiming(world, match, first, token="a1")
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=second))

    before = world.uow.commits
    ledger = await world.pay_for_a_seat.execute(
        PayForASeatCommand(
            match_id=match.id,
            player_id=second,
            amount=Grosze(int(SHARE)),
            reference=pay("a2"),
            channel=Online(settlement=pay("a2s")),
        )
    )

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert [seat.paid for seat in stored.seats] == [True, True, False, False]

    reservation = await world.reservations.for_match(match.id)
    assert reservation is not None

    assert await world.outbox("matches.seat_paid", "matches.court_held") == [
        "matches.seat_paid",
        "matches.seat_paid",
        "matches.court_held",
    ]

    # Two commits: the four rows, and then the movement. Never one — ADR-0055
    # refuses a movement inside a match transaction — and never three.
    assert world.uow.commits - before == 2
    assert ledger.movements[0].reservation == reservation.id


async def test_a_payment_that_earns_no_court_names_no_reservation(world):
    """One paid seat is no tier, so there is no court and the share funds none."""

    _, _, match = await a_match(world)
    ledger = await paid_by_claiming(world, match, uuid4(), token="b1")

    assert await world.reservations.for_match(match.id) is None
    assert ledger.movements[0].reservation is None


# ---------------------------------------------------------------------------
# 2. A failure anywhere in that write leaves none of the four rows
# ---------------------------------------------------------------------------


class _Boom(RuntimeError):
    """What an induced failure raises. Its own type, so a real bug is not one."""


def _explode():
    async def fail(*_args, **_kwargs):
        raise _Boom()

    return fail


@pytest.mark.parametrize(
    "sabotage",
    [
        pytest.param("reservations.add", id="the reservation write"),
        pytest.param("reservations.overlapping", id="the free-court scan"),
        pytest.param("matches.save", id="the match save"),
        pytest.param("events.publish_many", id="the outbox write"),
    ],
)
async def test_a_failure_anywhere_in_the_write_leaves_none_of_the_four_rows(
    world, sabotage
):
    """Three of the four rows. **The reservation is not asserted here, and the
    reason is the driver rather than the product.**

    A reservation is written inside ``begin_nested()`` — ADR-0035's savepoint,
    which is what lets a refused claim be re-asked instead of poisoning the
    transaction. On PostgreSQL that nests inside the open transaction and a
    rollback takes it with everything else. Under pysqlite it does not: the
    driver opens no transaction until it sees DML, so when the *first* DML of
    the write is the one inside the savepoint, ``SAVEPOINT`` runs in autocommit
    and ``RELEASE`` commits the row. Measured, not assumed — the same insert
    with any DML before it rolls back correctly.

    So the row survives here and would not in production, which is exactly the
    tree's rule for `tests/integration/`: a guarantee with no SQLite equivalent
    goes there. What is asserted here is everything SQLite *can* speak for, and
    ``held_since`` carries the same claim from the match's side — a match that
    is keeping a court and a match that is not are two different rows.
    """

    _, _, match = await a_match(world)
    first, second = uuid4(), uuid4()
    await paid_by_claiming(world, match, first, token="c1")

    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=second))
    seat_of_the_claim = (await world.matches.get(match.id)).live_claim_of(
        second, instant(world.clock.now())
    )
    assert seat_of_the_claim is not None

    target, attribute = sabotage.split(".")
    setattr(getattr(world, target), attribute, _explode())

    with pytest.raises(_Boom):
        await world.pay_for_a_seat.execute(
            PayForASeatCommand(
                match_id=match.id,
                player_id=second,
                amount=Grosze(int(SHARE)),
                reference=pay("c2"),
                channel=Online(settlement=pay("c2s")),
            )
        )

    await world.uow.rollback()

    stored = await world.matches.get(match.id)
    assert stored is not None
    # The seat is neither taken nor paid, the match is keeping no court, nothing
    # was announced about any of it, and no money was recorded against a seat
    # she never got.
    assert [seat.paid for seat in stored.seats] == [True, False, False, False]
    assert stored.seat_of(second) is None
    assert stored.held_since is None
    assert await world.outbox("matches.court_held", "matches.seat_paid") == [
        "matches.seat_paid"
    ]
    assert (await world.ledgers.load(second)).movements == ()


async def test_the_sabotage_is_what_makes_those_four_cases_fail(world):
    """The negative control: unsabotaged, the same payment writes all four rows.

    Without it the parametrised case above would pass just as well if the
    fixture had never been able to earn a court in the first place.
    """

    _, _, match = await a_match(world)
    await paid_by_claiming(world, match, uuid4(), token="d1")
    await paid_by_claiming(world, match, uuid4(), token="d2")

    assert await world.reservations.for_match(match.id) is not None
    assert await world.outbox("matches.court_held") == ["matches.court_held"]


# ---------------------------------------------------------------------------
# 3. No court to win: an inventory loss, and the money still lands
# ---------------------------------------------------------------------------


async def test_where_no_court_can_be_won_the_same_write_records_the_loss(world):
    """One court, two matches at the same hour: the second one loses inventory.

    ADR-0035's single story — *nothing was free* — recorded as a fact of the
    match rather than raised at a player who has just paid.
    """

    club, category, first = await a_match(world, courts=1)
    _, _, second = await a_match(world, club=club, category=category)

    await paid_by_claiming(world, first, uuid4(), token="e1")
    await paid_by_claiming(world, first, uuid4(), token="e2")
    assert await world.reservations.for_match(first.id) is not None

    await paid_by_claiming(world, second, uuid4(), token="e3")
    ledger = await paid_by_claiming(world, second, uuid4(), token="e4")

    stored = await world.matches.get(second.id)
    assert stored is not None
    assert stored.inventory_lost
    assert await world.reservations.for_match(second.id) is None

    # The payment landed correctly all the same.
    assert [seat.paid for seat in stored.seats] == [True, True, False, False]
    assert [movement.cause for movement in ledger.movements] == [
        MovementCause.SHARE_ONLINE
    ]
    assert ledger.movements[0].reservation is None
    assert await world.outbox("matches.inventory_lost") == ["matches.inventory_lost"]


# ---------------------------------------------------------------------------
# 4. Two custody regimes, two chains
# ---------------------------------------------------------------------------


async def test_an_open_matchs_share_is_held_by_raketa(world):
    _, _, match = await a_match(world)
    player = uuid4()

    ledger = await paid_by_claiming(world, match, player, token="f1")

    assert [movement.cause for movement in ledger.movements] == [
        MovementCause.SHARE_ONLINE
    ]
    assert ledger.movements[0].payer == PlayerParty(player)
    assert ledger.movements[0].payee == RaketaParty()
    assert ledger.held_for(SeatRef(match_id=match.id, index=0)) == int(SHARE)


async def test_a_private_courts_share_passes_through_on_arrival(world):
    club, _, match = await a_match(
        world, kind=MatchKind.PRIVATE, pay_model=PayModel.SPLIT, open_seats=2
    )
    player = uuid4()

    ledger = await paid_by_claiming(world, match, player, token="g1")

    assert [movement.cause for movement in ledger.movements] == [
        MovementCause.SHARE_ONLINE,
        MovementCause.SHARE_ONLINE,
    ]
    assert ledger.movements[0].payee == RaketaParty()
    assert ledger.movements[1].payer == RaketaParty()
    assert ledger.movements[1].payee == ClubParty(club.id)
    assert ledger.movements[1].reference == pay("g1s")
    # Raketa's position on that seat is zero from the same instant.
    assert ledger.held_for(SeatRef(match_id=match.id, index=0)) == 0


async def test_the_regime_is_the_matchs_answer_and_not_the_callers(world):
    """The same command, the same channel, two matches — two different chains.

    Custody follows what was sold (ADR-0056), so nothing on the command can
    move it. This is the pair of the two cases above stated as one claim.
    """

    club, category, open_match = await a_match(world)
    _, _, private = await a_match(
        world,
        club=club,
        category=category,
        kind=MatchKind.PRIVATE,
        open_seats=2,
        start=START + timedelta(hours=3),
    )

    on_open = await paid_by_claiming(world, open_match, uuid4(), token="h1")
    on_private = await paid_by_claiming(world, private, uuid4(), token="h2")

    assert len(on_open.movements) == 1
    assert len(on_private.movements) == 2


# ---------------------------------------------------------------------------
# 5. The seam: a seat that has gone, and a seat that is already hers
# ---------------------------------------------------------------------------


async def test_money_for_a_seat_that_has_gone_is_recorded_and_given_back(world):
    """Her five minutes ran out while the money was in flight (ADR-0081).

    Both movements land in one append, so there is no instant at which the
    stored ledger says Raketa kept 38 zł.
    """

    _, _, match = await a_match(world)
    player = uuid4()
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=player))
    world.clock.advance(timedelta(minutes=6))

    before = world.uow.commits
    ledger = await world.pay_for_a_seat.execute(
        PayForASeatCommand(
            match_id=match.id,
            player_id=player,
            amount=Grosze(int(SHARE)),
            reference=pay("i1"),
            channel=Online(settlement=pay("i1s")),
        )
    )

    # One money write, not two: the share and its reversal land together, so
    # the stored ledger is never momentarily a payment nobody gave back.
    assert world.uow.commits - before == 2

    assert [movement.cause for movement in ledger.movements] == [
        MovementCause.SHARE_ONLINE,
        MovementCause.CLAIM_LAPSED,
    ]
    assert [movement.reference.text for movement in ledger.movements] == [
        "PAY-i1",
        "REV-i1",
    ]
    assert ledger.movements[1].seat == SeatRef(match_id=match.id, index=0)
    assert ledger.held_for(SeatRef(match_id=match.id, index=0)) == 0

    # Nothing was written on the Matches side at all.
    stored = await world.matches.get(match.id)
    assert stored is not None
    assert stored.seat_of(player) is None


async def test_the_refund_names_the_seat_of_her_newest_claim(world):
    """Two lapsed claims on two seats, and the money is for the second one.

    Claims are ended and never removed — the cooldown is measured from the
    instant one closed — so both rows are still there to choose between, and
    the oldest is the attempt she already gave up on. A refund filed against
    seat 0 when she was buying seat 1 is a statement line that disagrees with
    what she did.
    """

    _, _, match = await a_match(world)
    player = uuid4()

    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=player))
    world.clock.advance(timedelta(minutes=6))
    # Somebody buys the seat she gave up on — which reaps her lapsed claim on
    # the way past — so her second attempt is seat 1.
    await paid_by_claiming(world, match, uuid4(), token="q0")
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=player))
    world.clock.advance(timedelta(minutes=6))

    stored = await world.matches.get(match.id)
    assert [
        claim.seat_index for claim in stored.claims if claim.player_id == player
    ] == [0, 1]

    ledger = await world.pay_for_a_seat.execute(
        PayForASeatCommand(
            match_id=match.id,
            player_id=player,
            amount=Grosze(int(SHARE)),
            reference=pay("q1"),
            channel=Online(settlement=pay("q1s")),
        )
    )

    assert {movement.seat for movement in ledger.movements} == {
        SeatRef(match_id=match.id, index=1)
    }


async def test_a_seat_that_is_already_hers_is_funded_and_never_refunded(world):
    """The state a process that died between the two transactions leaves behind.

    A replayed report finds a paid seat, writes no seat, and records the share
    the ledger is short. Read as *gone* instead, it would refund a seat she is
    sitting on.
    """

    _, _, match = await a_match(world)
    player = uuid4()
    await world.take.execute(TakeSeatCommand(match_id=match.id, player_id=player))

    ledger = await world.pay_for_a_seat.execute(
        PayForASeatCommand(
            match_id=match.id,
            player_id=player,
            amount=Grosze(int(SHARE)),
            reference=pay("j1"),
            channel=Online(settlement=pay("j1s")),
        )
    )
    assert [movement.cause for movement in ledger.movements] == [
        MovementCause.SHARE_ONLINE
    ]

    healed = await world.pay_for_a_seat.execute(
        PayForASeatCommand(
            match_id=match.id,
            player_id=player,
            amount=Grosze(int(SHARE)),
            reference=pay("j2"),
            channel=Online(settlement=pay("j2s")),
        )
    )
    assert [movement.cause for movement in healed.movements] == [
        MovementCause.SHARE_ONLINE,
        MovementCause.SHARE_ONLINE,
    ]


async def test_the_same_report_arriving_twice_is_refused_by_its_reference(world):
    """A duplicate delivery is the same event twice, and nothing happened twice.

    Refused rather than recorded and compensated: a compensation says something
    happened (ADR-0057).
    """

    _, _, match = await a_match(world)
    player = uuid4()
    await paid_by_claiming(world, match, player, token="k1")

    with pytest.raises(DuplicateMovementReference):
        await world.pay_for_a_seat.execute(
            PayForASeatCommand(
                match_id=match.id,
                player_id=player,
                amount=Grosze(int(SHARE)),
                reference=pay("k1"),
                channel=Online(settlement=pay("k1s")),
            )
        )

    assert len((await world.ledgers.load(player)).movements) == 1


async def test_money_naming_a_player_with_no_seat_and_no_claim_is_refused(world):
    """``shareOnline`` names a seat, so a payment that cannot name one is refused
    rather than filed against a guess."""

    _, _, match = await a_match(world)

    with pytest.raises(PaymentNamesNoSeat):
        await world.pay_for_a_seat.execute(
            PayForASeatCommand(
                match_id=match.id,
                player_id=uuid4(),
                amount=Grosze(int(SHARE)),
                reference=pay("l1"),
                channel=Online(settlement=pay("l1s")),
            )
        )


@pytest.mark.parametrize(
    "command",
    [
        pytest.param(
            dict(
                reference=Reference(ReferenceKind.REVERSAL, "r1"),
                channel=Online(settlement=pay("r1s")),
            ),
            id="the payment",
        ),
        pytest.param(
            dict(
                reference=pay("r2"),
                channel=Online(settlement=Reference(ReferenceKind.REFUND, "r2s")),
            ),
            id="the club settlement",
        ),
    ],
)
def test_a_seat_payment_is_filed_under_a_payment_reference(command):
    """Both references name money going out of a player's hands.

    The reconciliation reads compensations **by kind**, so a share filed under
    ``REV-`` would be counted as a correction of something and both `held` and
    the float would be wrong — silently, and in the one place the record is the
    answer to a dispute (ADR-0057). Refused where the command is built, so no
    use case has to remember it.
    """

    with pytest.raises(InvariantViolated):
        PayForASeatCommand(
            match_id=uuid4(),
            player_id=uuid4(),
            amount=Grosze(int(SHARE)),
            **command,
        )


async def test_a_payment_for_a_match_that_does_not_exist_is_refused(world):
    with pytest.raises(MatchNotFound):
        await world.pay_for_a_seat.execute(
            PayForASeatCommand(
                match_id=uuid4(),
                player_id=uuid4(),
                amount=Grosze(int(SHARE)),
                reference=pay("m1"),
                channel=Online(settlement=pay("m1s")),
            )
        )


# ---------------------------------------------------------------------------
# Cash across a counter
# ---------------------------------------------------------------------------


async def test_a_counter_paid_share_is_recorded_and_the_seat_reads_paid(world):
    """The one movement Raketa was never party to (ADR-0059).

    An invited player holds her seat already, so the club's mark is what pays
    it — and without the movement the seat reads unpaid for ever and the
    nightly seat-chain assertion never passes on a court with a cash payer.
    """

    club, _, match = await a_match(world)
    player = uuid4()
    await world.take.execute(TakeSeatCommand(match_id=match.id, player_id=player))

    ledger = await world.pay_for_a_seat.execute(
        PayForASeatCommand(
            match_id=match.id,
            player_id=player,
            amount=Grosze(int(SHARE)),
            reference=pay("n1"),
            channel=AcrossTheCounter(),
        )
    )

    assert [movement.cause for movement in ledger.movements] == [
        MovementCause.SHARE_AT_COUNTER
    ]
    assert ledger.movements[0].payer == PlayerParty(player)
    assert ledger.movements[0].payee == ClubParty(club.id)

    stored = await world.matches.get(match.id)
    assert stored is not None
    assert stored.seat_of(player).paid


async def test_a_counter_mark_for_a_seat_she_no_longer_holds_is_refused(world):
    """Reversing it would debit the club, and the club is only ever paid.

    ADR-0059's own remedy is that the club returns the cash at the counter —
    the party holding the money is the party who puts it right.
    """

    _, _, match = await a_match(world)
    player = uuid4()
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=player))
    world.clock.advance(timedelta(minutes=6))

    with pytest.raises(CounterShareNotOwed):
        await world.pay_for_a_seat.execute(
            PayForASeatCommand(
                match_id=match.id,
                player_id=player,
                amount=Grosze(int(SHARE)),
                reference=pay("o1"),
                channel=AcrossTheCounter(),
            )
        )

    assert (await world.ledgers.load(player)).movements == ()


# ---------------------------------------------------------------------------
# The funding chain, asserted the way the reconciliation asserts it
# ---------------------------------------------------------------------------


async def test_every_funding_chain_this_write_produces_closes(world):
    """AC: *every seat's funding chain closes* — the nightly job's own function.

    All four ways a share can arrive, each on its own ledger, then the same
    three invariants ``python -m app.reconciliation`` calls. A second copy of
    one of them here would be a second thing that can disagree about whether
    the ledger is sound.
    """

    club, category, open_match = await a_match(world)
    _, _, private = await a_match(
        world,
        club=club,
        category=category,
        kind=MatchKind.PRIVATE,
        open_seats=2,
        start=START + timedelta(hours=3),
    )

    held = uuid4()
    passed = uuid4()
    counter = uuid4()
    lapsed = uuid4()

    await paid_by_claiming(world, open_match, held, token="p1")
    await paid_by_claiming(world, private, passed, token="p2")

    await world.take.execute(TakeSeatCommand(match_id=open_match.id, player_id=counter))
    await world.pay_for_a_seat.execute(
        PayForASeatCommand(
            match_id=open_match.id,
            player_id=counter,
            amount=Grosze(int(SHARE)),
            reference=pay("p3"),
            channel=AcrossTheCounter(),
        )
    )

    await world.claim.execute(
        ClaimSeatCommand(match_id=open_match.id, player_id=lapsed)
    )
    world.clock.advance(timedelta(minutes=6))
    await world.pay_for_a_seat.execute(
        PayForASeatCommand(
            match_id=open_match.id,
            player_id=lapsed,
            amount=Grosze(int(SHARE)),
            reference=pay("p4"),
            channel=Online(settlement=pay("p4s")),
        )
    )

    for player in (held, passed, counter, lapsed):
        ledger = await world.ledgers.load(player)
        assert every_seat_chain_closes(ledger) == ()
        assert breaches_in(ledger) == ()


def test_the_chain_assertion_is_the_one_the_reconciliation_calls():
    """Pinned by identity, not by name: two copies would disagree eventually."""

    from app.modules.money.domain.invariants import LEDGER_INVARIANTS

    assert every_seat_chain_closes in LEDGER_INVARIANTS
