"""The exclusion constraint, on the real `reservations` table.

The sibling `test_interval_exclusion.py` asserts the *shape* against a throwaway
table, because when `Raketa02/Raketa#62` landed there was no `reservations` table
to point at. This file points at the real one: it is created from
`Base.metadata` — the same declarations the application maps to, and the same
ones `tests/unit/test_courts_migration.py` pins the migration against — inside a
throwaway schema that is dropped afterwards.

**Why here and nowhere else.** ADR-0035 names this as the sharpest cost of the
decision: *"PostgreSQL has it (`EXCLUDE USING gist` over a range), SQLite does
not — and the test suite runs on SQLite. The guarantee will therefore hold in
production and not in the fastest tests, so the exclusion needs a test that runs
against Postgres or it is being asserted by hope."* This is that test.

**Every case is paired with the same insert against the same table with the
constraint dropped by name.** So the positive case can no longer pass because
the row was refused for an unrelated reason, and the negative case can no longer
pass because the two intervals never overlapped.

The `search_path` includes `public` deliberately: `btree_gist`'s operator classes
live where the extension was installed, and `court_id WITH =` cannot resolve
without them. A scratch schema alone would fail at `ALTER TABLE`, which reads as
a broken test rather than as a missing extension.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.bootstrap.composition import (
    build_club_repository,
    build_reservation_repository,
    build_unit_of_work,
)
from app.infrastructure.clock import SystemClock
from app.kernel import Cover, Sport, hours, instant, zloty
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
    CourtLabel,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
)
from app.modules.courts.application.claim_court import ClaimCourt
from app.modules.courts.application.commands import ClaimCourtCommand
from app.modules.courts.domain.errors import InventoryLost
from app.modules.courts.domain.reservation import MatchHeld
from app.modules.courts.domain.time_range import span

from app.infrastructure.database import models as _models  # noqa: F401  (registers)
from app.infrastructure.database.base import Base
from app.modules.courts.infrastructure.sqlalchemy_court_models import (
    RESERVATION_EXCLUSION,
)
from app.modules.courts.infrastructure.sqlalchemy_reservation_repository import (
    COURT_IS_TAKEN,
)

pytestmark = pytest.mark.postgres

EXCLUSION_VIOLATION = "23P01"

MONDAY_1800 = datetime(2026, 8, 31, 18, 0, tzinfo=timezone.utc)

COURT_TABLES = (
    "clubs",
    "club_card_offsets",
    "club_policies",
    "club_payout_destinations",
    "club_court_categories",
    "club_court_catalogue",
    "reservations",
    "bookings",
)

INSERT = (
    "INSERT INTO reservations (id, club_id, court_id, category_id, "
    "played_from, played_to, claimed_from, claimed_to, holder_kind, "
    "booking_id, match_id, released_at, version) "
    "VALUES (:id, :club, :court, :category, :played_from, :played_to, "
    ":claimed_from, :claimed_to, 'club', NULL, NULL, :released_at, 0)"
)


@pytest.fixture
async def courts_schema(pg_engine):
    """The Clubs and Courts tables, from the application's own declarations.

    In a scratch schema dropped on the way out, failure included. `public` stays
    on the search path so `btree_gist` resolves.
    """

    schema = f"courts_guarantee_{uuid.uuid4().hex[:12]}"
    tables = [Base.metadata.tables[name] for name in COURT_TABLES]
    async with pg_engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        await connection.execute(text(f'SET search_path TO "{schema}", public'))
        # `checkfirst=False` is load-bearing, and it is `public` being on the
        # path that makes it so: an inspection would find the *migrated*
        # `public.clubs` on a developer's own database and skip creating the
        # scratch one, after which every insert here would land in the real
        # schema. `public` cannot simply be dropped from the path — `court_id
        # WITH =` resolves its GiST operator class through it, and `btree_gist`
        # can only be installed once per database.
        await connection.run_sync(
            Base.metadata.create_all, tables=tables, checkfirst=False
        )
    try:
        yield schema
    finally:
        async with pg_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


async def _run(pg_engine, schema, statement, **params):
    async with pg_engine.begin() as connection:
        await connection.execute(text(f'SET search_path TO "{schema}", public'))
        return await connection.execute(text(statement), params)


async def _scalar(pg_engine, schema, statement, **params):
    return (await _run(pg_engine, schema, statement, **params)).scalar_one()


async def _a_club(pg_engine, schema, name="Zabłocie Sport") -> uuid.UUID:
    club_id = uuid.uuid4()
    await _run(
        pg_engine,
        schema,
        "INSERT INTO clubs (id, name, address_line, address_city, "
        "address_postal_code, address_country, latitude, longitude, timezone, "
        "price_multiplier_num, price_multiplier_den, slot_discount_num, "
        "slot_discount_den, version) VALUES (:i, :n, 'ul. Zabłocie 25', "
        "'Kraków', '30-701', 'PL', 50.048100, 19.958500, 'Europe/Warsaw', "
        "100, 100, 100, 100, 0)",
        i=club_id,
        n=name,
    )
    return club_id


async def _a_category(pg_engine, schema, club_id, name="Padel · Mondo, indoor"):
    category_id = uuid.uuid4()
    await _run(
        pg_engine,
        schema,
        "INSERT INTO club_court_categories (id, club_id, name, sport, "
        "rate_grosze, retired_at) VALUES (:i, :c, :n, 'PADEL', 12000, NULL)",
        i=category_id,
        c=club_id,
        n=name,
    )
    return category_id


async def _claim(
    pg_engine,
    schema,
    club,
    category,
    court,
    *,
    start=MONDAY_1800,
    hours=1.0,
    turnaround=0.0,
    released_at=None,
):
    """One reservation. ``turnaround`` widens the claim past the play."""

    row_id = uuid.uuid4()
    played_to = start + timedelta(hours=hours)
    await _run(
        pg_engine,
        schema,
        INSERT,
        id=row_id,
        club=club,
        court=court,
        category=category,
        played_from=start,
        played_to=played_to,
        claimed_from=start,
        claimed_to=played_to + timedelta(hours=turnaround),
        released_at=released_at,
    )
    return row_id


async def _live_claims(pg_engine, schema, court):
    return await _scalar(
        pg_engine,
        schema,
        "SELECT count(*) FROM reservations WHERE court_id = :c "
        "AND released_at IS NULL",
        c=court,
    )


async def _drop_constraint(pg_engine, schema):
    """The negative control: the real constraint, removed by name."""

    await _run(
        pg_engine,
        schema,
        f'ALTER TABLE reservations DROP CONSTRAINT "{RESERVATION_EXCLUSION}"',
    )


@pytest.fixture
async def venue(pg_engine, courts_schema):
    club = await _a_club(pg_engine, courts_schema)
    category = await _a_category(pg_engine, courts_schema, club)
    return courts_schema, club, category


# --- the constraint exists and says what it was declared to say -------------


async def test_the_exclusion_constraint_is_on_the_real_table(pg_engine, venue):
    """Read back from the catalog, so it is what PostgreSQL believes and not
    what the declaration said."""

    schema, _, _ = venue
    definition = await _scalar(
        pg_engine,
        schema,
        "SELECT pg_get_constraintdef(c.oid) FROM pg_constraint c "
        "JOIN pg_namespace n ON n.oid = c.connamespace "
        "WHERE c.conname = :name AND n.nspname = :namespace",
        name=RESERVATION_EXCLUSION,
        namespace=schema,
    )

    assert definition.startswith("EXCLUDE USING gist"), definition
    assert "court_id WITH =" in definition, definition
    assert "WITH &&" in definition, definition
    assert "released_at IS NULL" in definition, definition


# --- overlap on one court ---------------------------------------------------


async def test_two_reservations_overlapping_on_one_court_are_refused(pg_engine, venue):
    schema, club, category = venue
    court = uuid.uuid4()
    await _claim(pg_engine, schema, club, category, court)

    with pytest.raises(IntegrityError) as exc:
        await _claim(
            pg_engine,
            schema,
            club,
            category,
            court,
            start=MONDAY_1800 + timedelta(minutes=30),
        )

    assert getattr(exc.value.orig, "sqlstate", None) == EXCLUSION_VIOLATION, (
        "the second claim was refused, but not by the exclusion constraint"
    )
    assert await _live_claims(pg_engine, schema, court) == 1


async def test_without_the_constraint_the_court_is_taken_twice(pg_engine, venue):
    """The negative control. Without it, the case above would still pass if the
    two intervals had simply never overlapped."""

    schema, club, category = venue
    court = uuid.uuid4()
    await _drop_constraint(pg_engine, schema)

    await _claim(pg_engine, schema, club, category, court)
    await _claim(
        pg_engine,
        schema,
        club,
        category,
        court,
        start=MONDAY_1800 + timedelta(minutes=30),
    )

    assert await _live_claims(pg_engine, schema, court) == 2


async def test_a_claim_wholly_inside_another_is_refused(pg_engine, venue):
    """The dead repo's `#127`, from the schema side: a rule about a slot's
    *start* would accept this."""

    schema, club, category = venue
    court = uuid.uuid4()
    await _claim(pg_engine, schema, club, category, court, hours=2)

    with pytest.raises(IntegrityError) as exc:
        await _claim(
            pg_engine,
            schema,
            club,
            category,
            court,
            start=MONDAY_1800 + timedelta(minutes=30),
            hours=0.5,
        )

    assert getattr(exc.value.orig, "sqlstate", None) == EXCLUSION_VIOLATION


async def test_two_courts_may_hold_the_same_hour(pg_engine, venue):
    schema, club, category = venue
    first, second = uuid.uuid4(), uuid.uuid4()

    await _claim(pg_engine, schema, club, category, first)
    await _claim(pg_engine, schema, club, category, second)

    assert await _live_claims(pg_engine, schema, first) == 1
    assert await _live_claims(pg_engine, schema, second) == 1


async def test_back_to_back_reservations_on_one_court_are_accepted(pg_engine, venue):
    """Half-open `[)`: a court freed at 19:00 and taken at 19:00 do not overlap.

    Which is what lets `turnaroundMin` widen a claim by padding rather than by
    arithmetic on somebody else's row.
    """

    schema, club, category = venue
    court = uuid.uuid4()

    await _claim(pg_engine, schema, club, category, court)
    await _claim(
        pg_engine, schema, club, category, court, start=MONDAY_1800 + timedelta(hours=1)
    )

    assert await _live_claims(pg_engine, schema, court) == 2


async def test_a_turnaround_widens_what_the_constraint_refuses(pg_engine, venue):
    """The claimed interval is what excludes, and it is not the played one.

    18:00–19:00 played with a quarter-hour turnaround refuses a 19:00 start and
    accepts a 19:15 one — enforced by the database, on the same column the
    domain widened.
    """

    schema, club, category = venue
    court = uuid.uuid4()
    await _claim(pg_engine, schema, club, category, court, turnaround=0.25)

    with pytest.raises(IntegrityError) as exc:
        await _claim(
            pg_engine,
            schema,
            club,
            category,
            court,
            start=MONDAY_1800 + timedelta(hours=1),
        )
    assert getattr(exc.value.orig, "sqlstate", None) == EXCLUSION_VIOLATION

    await _claim(
        pg_engine,
        schema,
        club,
        category,
        court,
        start=MONDAY_1800 + timedelta(hours=1, minutes=15),
    )
    assert await _live_claims(pg_engine, schema, court) == 2


# --- released, never deleted ------------------------------------------------


async def test_a_released_claim_stops_excluding_and_keeps_its_row(pg_engine, venue):
    """The constraint is partial, which is what makes *released, never deleted*
    affordable: the withdrawn hold stays answerable and blocks nobody."""

    schema, club, category = venue
    court = uuid.uuid4()
    withdrawn = await _claim(pg_engine, schema, club, category, court)
    await _run(
        pg_engine,
        schema,
        "UPDATE reservations SET released_at = :t WHERE id = :i",
        t=MONDAY_1800 - timedelta(hours=6),
        i=withdrawn,
    )

    await _claim(pg_engine, schema, club, category, court)

    assert await _live_claims(pg_engine, schema, court) == 1
    assert (
        await _scalar(
            pg_engine,
            schema,
            "SELECT count(*) FROM reservations WHERE court_id = :c",
            c=court,
        )
        == 2
    )


async def test_two_released_claims_on_one_court_and_hour_are_both_kept(
    pg_engine, venue
):
    """History repeats. A court that has been claimed and released four times
    has four rows for one hour, which is the whole reason the constraint is
    partial rather than total."""

    schema, club, category = venue
    court = uuid.uuid4()
    for _ in range(4):
        await _claim(
            pg_engine,
            schema,
            club,
            category,
            court,
            released_at=MONDAY_1800 - timedelta(hours=6),
        )

    assert await _live_claims(pg_engine, schema, court) == 0
    assert (
        await _scalar(
            pg_engine,
            schema,
            "SELECT count(*) FROM reservations WHERE court_id = :c",
            c=court,
        )
        == 4
    )


# --- the race ---------------------------------------------------------------


async def test_two_writers_racing_for_one_court_resolve_as_one_winner(
    pg_engine, venue
):
    """ADR-0035's C1, run: *"Two open matches, same club, category and hour."*

    One row lands and one writer is refused. **Which refusal is not fixed**, and
    that is a property of the constraint rather than a flake: a GiST exclusion
    index inserts its entry before it scans for a conflict, so exactly
    simultaneous writers can each find the other's pending entry and wait, and
    PostgreSQL breaks the cycle by aborting one with ``40P01``. Measured here at
    roughly one race in four. Both codes mean *somebody else reached this court*,
    both leave nothing behind, and `SqlAlchemyReservationRepository` translates
    both — which is why the assertion is on the **set** of legal answers rather
    than on one, and why a third code would fail it.
    """

    schema, club, category = venue
    court = uuid.uuid4()

    async def claim():
        try:
            await _claim(pg_engine, schema, club, category, court)
            return None
        except DBAPIError as error:
            return getattr(error.orig, "sqlstate", None)

    outcomes = await asyncio.gather(claim(), claim())

    winners = [o for o in outcomes if o is None]
    losers = [o for o in outcomes if o is not None]
    assert len(winners) == 1, outcomes
    assert len(losers) == 1, outcomes
    assert losers[0] in COURT_IS_TAKEN, (
        f"the loser was refused with {losers[0]}, which the repository does not "
        "translate — it would reach a player as a 500"
    )
    assert await _live_claims(pg_engine, schema, court) == 1


async def test_a_racing_claim_leaves_no_partial_write(pg_engine, venue):
    """*"never a lock timeout or a partial write"*. The loser wrote nothing at
    all, so the table holds exactly the winner's row and no orphan."""

    schema, club, category = venue
    court = uuid.uuid4()

    async def claim():
        try:
            await _claim(pg_engine, schema, club, category, court)
        except DBAPIError:
            pass

    await asyncio.gather(claim(), claim(), claim(), claim())

    assert (
        await _scalar(
            pg_engine,
            schema,
            "SELECT count(*) FROM reservations WHERE court_id = :c",
            c=court,
        )
        == 1
    )


async def test_without_the_constraint_both_writers_win(pg_engine, venue):
    """The negative control for the race: this is the defect ADR-0035 removed —
    expensive, silent and terminal, because `inventoryLost` cancels the match
    and refunds everybody."""

    schema, club, category = venue
    court = uuid.uuid4()
    await _drop_constraint(pg_engine, schema)

    async def claim():
        await _claim(pg_engine, schema, club, category, court)

    await asyncio.gather(claim(), claim())

    assert await _live_claims(pg_engine, schema, court) == 2


# --- the use case above the constraint --------------------------------------
#
# Everything above asserts what the *database* does. These assert what a caller
# gets, which is the acceptance criterion in its own words: *"two reservations
# racing for the same court in the same instant resolve as one winner and one
# query result — never a lock timeout or a partial write."* The unit suite
# cannot reach this: SQLite has no constraint to lose to, so there the refusal
# is a stub. Here it is the real one, produced by a real race.


@pytest.fixture
async def schema_sessions(courts_schema, postgres_url):
    """Sessions whose connections open with the scratch schema on the path.

    Baked into the connection rather than issued per statement, so the use case
    under test runs exactly as it runs in production — no fixture is reaching
    into its session between calls.
    """

    engine = create_async_engine(
        postgres_url,
        poolclass=NullPool,
        connect_args={
            "server_settings": {"search_path": f"{courts_schema},public"}
        },
    )
    try:
        yield async_sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
    finally:
        await engine.dispose()


async def _a_venue_through_the_use_cases(sessions, *, courts: int):
    """One club, one category, `courts` courts — written the way a request would."""

    async with sessions() as session:
        clubs = build_club_repository(session)
        uow = build_unit_of_work(session)
        clock = SystemClock()
        club = await RegisterClub(clubs, uow, clock).execute(
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
                payout=PayoutDestination(
                    account_holder="Zabłocie", iban="PL00000000000000000000000000"
                ),
            )
        )
        category = await AddCourtCategory(clubs, uow, clock).execute(
            AddCourtCategoryCommand(
                club_id=club.id,
                name=CategoryName("Padel · Mondo, indoor"),
                sport=Sport.PADEL,
                cover=Cover.INDOOR,
                rate=zloty(120),
            )
        )
        for index in range(courts):
            await AddCourt(clubs, uow, clock).execute(
                AddCourtCommand(
                    club_id=club.id,
                    category_id=category.id,
                    label=CourtLabel(f"Court {index + 1}"),
                )
            )
    return club.id, category.id


async def _claim_through_the_use_case(sessions, club_id, category_id):
    async with sessions() as session:
        claim = ClaimCourt(
            build_club_repository(session),
            build_reservation_repository(session),
            build_unit_of_work(session),
        )
        try:
            reservation = await claim.execute(
                ClaimCourtCommand(
                    club_id=club_id,
                    category_id=category_id,
                    played=span(
                        instant(MONDAY_1800), hours(1)
                    ),
                    holder=MatchHeld(uuid.uuid4()),
                )
            )
            return reservation.court_id
        except InventoryLost:
            return "inventory lost"


async def test_two_matches_racing_on_two_courts_each_get_a_different_one(
    pg_engine, schema_sessions
):
    """*"Each gets a genuinely different court"* — with the mechanism it never
    had. The loser is re-asked and lands on the other court; nobody is told
    anything about a race."""

    club_id, category_id = await _a_venue_through_the_use_cases(
        schema_sessions, courts=2
    )

    first, second = await asyncio.gather(
        _claim_through_the_use_case(schema_sessions, club_id, category_id),
        _claim_through_the_use_case(schema_sessions, club_id, category_id),
    )

    assert "inventory lost" not in (first, second), (first, second)
    assert first != second


async def test_two_matches_racing_on_one_court_produce_one_winner_and_one_story(
    pg_engine, schema_sessions
):
    """The loser hears `inventoryLost` — a query result, and the only story
    ADR-0035 lets a player be told."""

    club_id, category_id = await _a_venue_through_the_use_cases(
        schema_sessions, courts=1
    )

    outcomes = await asyncio.gather(
        _claim_through_the_use_case(schema_sessions, club_id, category_id),
        _claim_through_the_use_case(schema_sessions, club_id, category_id),
    )

    assert outcomes.count("inventory lost") == 1, outcomes
    async with schema_sessions() as session:
        stored = await session.execute(text("SELECT count(*) FROM reservations"))
        assert stored.scalar_one() == 1
