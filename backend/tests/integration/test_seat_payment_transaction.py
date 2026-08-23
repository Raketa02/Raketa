"""The fourth row: a seat payment's reservation is in the payment's transaction.

``Raketa02/Raketa#70``, and this file exists for one row that SQLite cannot
speak for. ADR-0035: *"a seat payment that earns a court, and the court it
earns, are one event or they are a bug"*, so the write carries the seat, the
reservation **or** the inventory loss, and the outbox rows for both.
``tests/unit/test_seat_payment.py`` asserts three of those four rows against
in-memory SQLite in milliseconds. The reservation is here.

**Why it cannot be there.** A reservation is written inside ``begin_nested()``
— ADR-0035's savepoint, which is what lets a refused claim be re-asked instead
of poisoning the transaction. Under pysqlite the driver opens no transaction
until it sees DML, so when the *first* DML of a write is the one inside the
savepoint, ``SAVEPOINT`` runs in autocommit and ``RELEASE`` commits the row: a
rollback then leaves it standing. Measured rather than reasoned about — the same
insert with any DML before it rolls back correctly, and on PostgreSQL, where the
transaction is genuinely open, so does this one. That is precisely the shape the
README's *Which suite owns a Postgres-only case* sends here.

**It carries its own negative control**, because an atomicity assertion written
against a transaction that already held has never been observed to fail, which
is indistinguishable from not working. The control commits at the point the
product does not, and the same case then finds the reservation standing.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

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
from app.infrastructure.database import models as _models  # noqa: F401  (registers)
from app.infrastructure.database.base import Base
from app.kernel import Grosze, SeatShare, Sport, grosze, hours, instant, zloty
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
)
from app.modules.matches.application.post_match import PostMatch
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.application.seat_moves import ClaimSeat
from app.modules.money.application.commands import Online, PayForASeatCommand
from app.modules.money.application.pay_for_a_seat import PayForASeat
from app.modules.money.application.record_movements import RecordMovements
from app.modules.money.application.record_share import RecordShare
from app.modules.money.domain.reference import Reference, ReferenceKind

pytestmark = pytest.mark.postgres

START = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))
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


class _Boom(RuntimeError):
    """What the induced failure raises. Its own type, so a real bug is not one."""


class _AnybodyMayClaim:
    """The cross-match *is she buying a seat elsewhere* read, answering *no*."""

    async def live_for(self, player_id, *, at):
        return None


@pytest.fixture
async def payment_schema(pg_engine):
    """Every application table, in a scratch schema dropped on the way out.

    All of ``Base.metadata`` rather than a hand-listed subset: this write spans
    Clubs, Courts, Matches, the event store and the outbox, and a list of the
    tables it happens to touch today is one that goes stale the first time any
    of those contexts grows a table. ``public`` stays on the path so
    ``btree_gist`` resolves for the reservations exclusion.
    """

    schema = f"seat_payment_{uuid.uuid4().hex[:12]}"
    async with pg_engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        await connection.execute(text(f'SET search_path TO "{schema}", public'))
        # `checkfirst=False`, for the reason `test_reservation_exclusion.py`
        # gives: with `public` on the path an inspection would find a migrated
        # table on a developer's own database and skip creating the scratch one,
        # after which every write here would land in the real schema.
        await connection.run_sync(Base.metadata.create_all, checkfirst=False)
    try:
        yield schema
    finally:
        async with pg_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


@pytest.fixture
async def sessions(payment_schema, postgres_url):
    """Sessions whose connections open with the scratch schema on the path."""

    engine = create_async_engine(
        postgres_url,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": f"{payment_schema},public"}},
    )
    try:
        yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    finally:
        await engine.dispose()


class _World:
    """Clubs, Courts, Matches and Money over one session — the request's wiring."""

    def __init__(self, session, clock) -> None:
        clubs = build_club_repository(session)
        self.events = build_event_publisher(session)
        self.reservations = build_reservation_repository(session)
        self.matches = build_match_repository(session, events=self.events, clock=clock)
        self.uow = build_unit_of_work(session)

        holds = ResolveCourtHold(
            self.matches,
            build_court_holds(
                ClaimCourt(clubs, self.reservations, self.uow), self.reservations
            ),
            self.uow,
            clock,
        )
        ledgers = build_ledger_repository(
            event_store=build_domain_event_store(session), events=self.events
        )
        movements = RecordMovements(ledgers, self.uow, clock)
        self.pay_for_a_seat = PayForASeat(
            build_seats(
                matches=self.matches, holds=holds, reservations=self.reservations
            ),
            RecordShare(movements),
            movements,
            self.uow,
            clock,
        )

        self.register_club = RegisterClub(clubs, self.uow, clock)
        self.add_category = AddCourtCategory(clubs, self.uow, clock)
        self.add_court = AddCourt(clubs, self.uow, clock)
        self.post = PostMatch(self.matches, clubs, holds, self.uow, clock)
        self.claim = ClaimSeat(self.matches, holds, self.uow, clock, _AnybodyMayClaim())


async def _a_match_one_payment_short_of_a_court(world):
    """A club, a court, a match, and one paid seat — so the next one grants."""

    club = await world.register_club.execute(
        RegisterClubCommand(
            name=ClubName(f"Zabłocie {uuid.uuid4().hex[:6]}"),
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
            club_id=club.id, category_id=category.id, label=CourtLabel("Court 1")
        )
    )
    match = await world.post.execute(
        PostMatchCommand(
            club_id=club.id,
            category_id=category.id,
            sport=Sport.PADEL,
            start=START,
            duration=hours(1),
            share=SHARE,
        )
    )

    first = uuid.uuid4()
    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=first))
    await world.pay_for_a_seat.execute(
        PayForASeatCommand(
            match_id=match.id,
            player_id=first,
            amount=Grosze(int(SHARE)),
            reference=pay("first"),
            channel=Online(settlement=pay("firsts")),
        )
    )
    assert await world.reservations.for_match(match.id) is None
    return match


async def _pay_and_fail(world, match, *, player, commit_before_failing):
    """The second payment, exploding after the reservation has been written.

    ``matches.save`` is what breaks, which is the point *after* the court has
    been kept aside and *before* the transaction closes — the exact window this
    file is about.
    """

    await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=player))

    original = world.matches.save

    async def save(*args, **kwargs):
        if commit_before_failing:
            await world.uow.commit()
        raise _Boom()

    world.matches.save = save
    try:
        with pytest.raises(_Boom):
            await world.pay_for_a_seat.execute(
                PayForASeatCommand(
                    match_id=match.id,
                    player_id=player,
                    amount=Grosze(int(SHARE)),
                    reference=pay("second"),
                    channel=Online(settlement=pay("seconds")),
                )
            )
    finally:
        world.matches.save = original
    await world.uow.rollback()


async def test_a_failed_seat_payment_leaves_no_reservation_behind(sessions):
    """The claim: the court the payment earned goes with the payment.

    Without it the match's row rolls back and the court does not, so the club
    has a reservation nobody can explain, held for a match that never entered a
    tier — inventory out of circulation until somebody notices by hand.
    """

    clock = _Clock(START - timedelta(days=14))
    async with sessions() as session:
        world = _World(session, clock)
        match = await _a_match_one_payment_short_of_a_court(world)

        await _pay_and_fail(
            world, match, player=uuid.uuid4(), commit_before_failing=False
        )

        assert await world.reservations.for_match(match.id) is None
        stored = await world.matches.get(match.id)
        assert stored is not None
        assert stored.held_since is None
        assert [seat.paid for seat in stored.seats] == [True, False, False, False]


async def test_the_same_case_finds_the_reservation_when_the_write_is_split(sessions):
    """The negative control, and it is what makes the case above mean anything.

    The only difference is a commit where the product has none. If a savepoint
    were leaking the row out of the transaction — which is exactly what happens
    under pysqlite — the case above would pass for a reason that has nothing to
    do with the code it is asserting, and this one could not tell the difference.
    """

    clock = _Clock(START - timedelta(days=14))
    async with sessions() as session:
        world = _World(session, clock)
        match = await _a_match_one_payment_short_of_a_court(world)

        await _pay_and_fail(
            world, match, player=uuid.uuid4(), commit_before_failing=True
        )

        assert await world.reservations.for_match(match.id) is not None


async def test_a_seat_payment_that_earns_a_court_commits_all_four_rows(sessions):
    """And unsabotaged, the same payment leaves all four rows standing.

    The positive half: an atomicity assertion that only ever sees the failing
    path cannot tell *nothing was written* from *nothing was ever writable*.
    """

    clock = _Clock(START - timedelta(days=14))
    async with sessions() as session:
        world = _World(session, clock)
        match = await _a_match_one_payment_short_of_a_court(world)

        player = uuid.uuid4()
        await world.claim.execute(ClaimSeatCommand(match_id=match.id, player_id=player))
        ledger = await world.pay_for_a_seat.execute(
            PayForASeatCommand(
                match_id=match.id,
                player_id=player,
                amount=Grosze(int(SHARE)),
                reference=pay("second"),
                channel=Online(settlement=pay("seconds")),
            )
        )

        reservation = await world.reservations.for_match(match.id)
        assert reservation is not None
        stored = await world.matches.get(match.id)
        assert stored is not None
        assert stored.held_since is not None
        assert [seat.paid for seat in stored.seats] == [True, True, False, False]

        announced = (
            (
                await session.execute(
                    text(
                        "SELECT event_type FROM event_delivery_queue "
                        "WHERE event_type IN "
                        "('matches.seat_paid', 'matches.court_held')"
                    )
                )
            )
            .scalars()
            .all()
        )
        assert sorted(announced) == [
            "matches.court_held",
            "matches.seat_paid",
            "matches.seat_paid",
        ]

        # And the share names the court it earned.
        assert ledger.movements[0].reservation == reservation.id
