"""Claiming, reassigning and releasing a court — through the use cases, on disk.

Everything here runs on the ordinary SQLite fixture and reaches the database
through the same use cases a request would, wired from the composition root.
Nothing in this file writes a table.

**What SQLite cannot do is exactly one thing, and it is named rather than
skipped.** There is no `EXCLUDE USING gist` here, so the *race* — two writers
reaching one court in the same instant — is asserted in
`tests/integration/test_reservation_exclusion.py` against a real PostgreSQL. What
is asserted here is everything that does not need it: the ordinary scan-and-claim
path, the turnaround, the retry a refusal triggers (driven by a stub that raises
what the constraint raises), and the one story a player is ever told.

The stub is not a stand-in for the constraint. It is a stand-in for *losing*,
which is a thing the use case has to handle however the loss is detected — and
that logic has no database in it at all.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import (
    build_booking_repository,
    build_club_repository,
    build_reservation_repository,
    build_unit_of_work,
)
from app.infrastructure.clock import SystemClock
from app.kernel import Sport, hours, instant, minutes, percent, zloty
from app.modules.clubs.application.add_court import AddCourt
from app.modules.clubs.application.add_court_category import AddCourtCategory
from app.modules.clubs.application.commands import (
    AddCourtCategoryCommand,
    AddCourtCommand,
    RegisterClubCommand,
    RetireCourtCategoryCommand,
    RetireCourtCommand,
)
from app.modules.clubs.application.register_club import RegisterClub
from app.modules.clubs.application.retire_court import RetireCourt
from app.modules.clubs.application.retire_court_category import RetireCourtCategory
from app.modules.clubs.domain.errors import ClubNotFound
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
from app.modules.courts.application.book_court import BookCourt
from app.modules.courts.application.claim_court import ClaimCourt
from app.modules.courts.application.commands import (
    BookCourtCommand,
    ClaimCourtCommand,
    CourtAvailabilityQuery,
    ReassignCourtCommand,
    ReleaseReservationCommand,
)
from app.modules.courts.application.court_availability import (
    CourtAvailability,
    CourtHistory,
)
from app.modules.courts.application.reassign_court import ReassignCourt
from app.modules.courts.application.release_reservation import ReleaseReservation
from app.modules.courts.domain.errors import (
    ConcurrentReservationModification,
    CourtAlreadyClaimed,
    CourtNotInCategory,
    InventoryLost,
    ReservationNotFound,
)
from app.modules.courts.domain.reservation import (
    ClubHeld,
    HolderKind,
    MatchHeld,
    Reservation,
)
from app.modules.courts.domain.time_range import span
from app.modules.courts.infrastructure import (
    sqlalchemy_reservation_repository as reservation_repository_module,
)
from app.modules.courts.infrastructure.sqlalchemy_court_models import (
    BookingORM,
    ReservationORM,
)

TURNAROUND = minutes(15)


def at(hour: int, minute: int = 0, day: int = 1):
    return instant(datetime(2026, 9, day, hour, minute, tzinfo=timezone.utc))


EVENING = span(at(18), hours(1))


class _Courts:
    """Every use case this file drives, over one session."""

    def __init__(self, session, clock):
        clubs = build_club_repository(session)
        reservations = build_reservation_repository(session)
        bookings = build_booking_repository(session)
        uow = build_unit_of_work(session)

        self.session = session
        self.clubs = clubs
        self.reservations = reservations
        self.bookings = bookings

        self.register_club = RegisterClub(clubs, uow, clock)
        self.add_category = AddCourtCategory(clubs, uow, clock)
        self.retire_category = RetireCourtCategory(clubs, uow, clock)
        self.add_court = AddCourt(clubs, uow, clock)
        self.retire_court = RetireCourt(clubs, uow, clock)

        self.claim = ClaimCourt(clubs, reservations, uow)
        self.book = BookCourt(clubs, bookings, self.claim, uow, clock)
        self.reassign = ReassignCourt(clubs, reservations, uow)
        self.release = ReleaseReservation(reservations, uow, clock)
        self.availability = CourtAvailability(clubs, reservations)
        self.history = CourtHistory(reservations)

    async def a_club(self, *, name="Zabłocie Sport", turnaround=minutes(0), courts=3):
        club = await self.register_club.execute(
            RegisterClubCommand(
                name=ClubName(name),
                address=StreetAddress(
                    line="ul. Zabłocie 25", city="Kraków", postal_code="30-701"
                ),
                point=GeoPoint(
                    latitude=Decimal("50.048100"), longitude=Decimal("19.958500")
                ),
                timezone="Europe/Warsaw",
                policy=ClubPolicy(turnaround_min=turnaround),
                payout=PayoutDestination(
                    account_holder=name, iban="PL00000000000000000000000000"
                ),
                pricing=ClubPricing(price_multiplier=percent(100)),
            )
        )
        category = await self.add_category.execute(
            AddCourtCategoryCommand(
                club_id=club.id,
                name=CategoryName("Padel · Mondo, indoor"),
                sport=Sport.PADEL,
                rate=zloty(120),
            )
        )
        court_ids = []
        for index in range(courts):
            court = await self.add_court.execute(
                AddCourtCommand(
                    club_id=club.id,
                    category_id=category.id,
                    label=CourtLabel(f"Court {index + 1}"),
                )
            )
            court_ids.append(court.id)
        return club, category, tuple(court_ids)


@pytest.fixture
def clock():
    return SystemClock()


@pytest.fixture
async def courts(session_factory, clock):
    async with session_factory() as session:
        yield _Courts(session, clock)


async def count(session_factory, model, **where):
    async with session_factory() as session:
        statement = select(func.count()).select_from(model)
        for column, value in where.items():
            statement = statement.where(getattr(model, column) == value)
        return (await session.execute(statement)).scalar_one()


# --- the ordinary path ------------------------------------------------------


async def test_a_claim_reads_back_whole(courts, session_factory):
    club, category, court_ids = await courts.a_club()
    match_id = uuid.uuid4()

    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(match_id),
        )
    )

    stored = await courts.reservations.get(reservation.id)
    assert stored is not None
    assert stored.club_id == club.id
    assert stored.court_id in court_ids
    assert stored.category_id == category.id
    assert stored.played == EVENING
    assert stored.claimed == EVENING
    assert stored.holder == MatchHeld(match_id)
    assert stored.is_live
    assert stored.version == 0
    assert await count(session_factory, ReservationORM) == 1


def test_a_caller_names_a_category_and_never_a_court():
    """*"It never learns how courts are organised"* — stated where it can fail.

    ADR-0035: *"The match does not reach into court inventory. It asks for a
    court of this category, for this window, and is given a reservation or
    refused."* The absence is the context's whole interface promise, so it is
    asserted as an absence.
    """

    assert "court_id" not in ClaimCourtCommand.__dataclass_fields__
    assert "court_id" not in BookCourtCommand.__dataclass_fields__


async def test_the_first_free_court_is_taken_and_then_the_next(courts):
    club, category, court_ids = await courts.a_club()

    taken = []
    for _ in range(3):
        reservation = await courts.claim.execute(
            ClaimCourtCommand(
                club_id=club.id,
                category_id=category.id,
                played=EVENING,
                holder=MatchHeld(uuid.uuid4()),
            )
        )
        taken.append(reservation.court_id)

    assert sorted(taken, key=str) == sorted(court_ids, key=str)


async def test_a_fourth_claim_on_three_courts_is_inventory_lost(courts):
    club, category, _ = await courts.a_club(courts=3)
    for _ in range(3):
        await courts.claim.execute(
            ClaimCourtCommand(
                club_id=club.id,
                category_id=category.id,
                played=EVENING,
                holder=MatchHeld(uuid.uuid4()),
            )
        )

    with pytest.raises(InventoryLost):
        await courts.claim.execute(
            ClaimCourtCommand(
                club_id=club.id,
                category_id=category.id,
                played=EVENING,
                holder=MatchHeld(uuid.uuid4()),
            )
        )


async def test_a_second_claim_at_another_hour_is_ordinary(courts):
    club, category, _ = await courts.a_club(courts=1)
    await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )

    later = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=span(at(20), hours(1)),
            holder=MatchHeld(uuid.uuid4()),
        )
    )

    assert later.is_live


async def test_an_unknown_club_is_a_refusal(courts):
    with pytest.raises(ClubNotFound):
        await courts.claim.execute(
            ClaimCourtCommand(
                club_id=uuid.uuid4(),
                category_id=uuid.uuid4(),
                played=EVENING,
                holder=ClubHeld(),
            )
        )


async def test_a_retired_category_is_inventory_lost_and_not_a_not_found(courts):
    """ADR-0079: *no free court* and *no courts at all* are one answer. A
    category nobody may sell existed — the player's story is that there is
    nothing to have."""

    club, category, _ = await courts.a_club()
    await courts.retire_category.execute(
        RetireCourtCategoryCommand(club_id=club.id, category_id=category.id)
    )

    with pytest.raises(InventoryLost):
        await courts.claim.execute(
            ClaimCourtCommand(
                club_id=club.id,
                category_id=category.id,
                played=EVENING,
                holder=ClubHeld(),
            )
        )


async def test_a_retired_court_is_not_offered(courts):
    club, category, court_ids = await courts.a_club(courts=1)
    await courts.retire_court.execute(
        RetireCourtCommand(club_id=club.id, court_id=court_ids[0])
    )

    with pytest.raises(InventoryLost):
        await courts.claim.execute(
            ClaimCourtCommand(
                club_id=club.id,
                category_id=category.id,
                played=EVENING,
                holder=ClubHeld(),
            )
        )


# --- the turnaround ---------------------------------------------------------


async def test_our_own_claim_carries_the_clubs_turnaround(courts):
    club, category, _ = await courts.a_club(turnaround=TURNAROUND)

    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )

    assert reservation.played == EVENING
    assert reservation.claimed.end == at(19, 15)


async def test_a_club_published_block_is_never_padded(courts):
    club, category, _ = await courts.a_club(turnaround=TURNAROUND)

    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=ClubHeld(),
        )
    )

    assert reservation.claimed == reservation.played == EVENING


async def test_the_turnaround_takes_the_next_slot_off_the_same_court(courts):
    """One court, one turnaround: 19:00 is refused and 19:15 is not."""

    club, category, _ = await courts.a_club(courts=1, turnaround=TURNAROUND)
    await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )

    with pytest.raises(InventoryLost):
        await courts.claim.execute(
            ClaimCourtCommand(
                club_id=club.id,
                category_id=category.id,
                played=span(at(19), hours(1)),
                holder=MatchHeld(uuid.uuid4()),
            )
        )

    accepted = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=span(at(19, 15), hours(1)),
            holder=MatchHeld(uuid.uuid4()),
        )
    )
    assert accepted.is_live


async def test_the_played_interval_is_what_a_reader_is_given(courts):
    """The player is shown the game, never the claim it took."""

    club, category, _ = await courts.a_club(turnaround=TURNAROUND)

    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )
    stored = await courts.reservations.get(reservation.id)

    assert stored.played == EVENING
    assert stored.claimed != stored.played


# --- availability -----------------------------------------------------------


async def test_availability_is_computed_from_reservations(courts):
    club, category, court_ids = await courts.a_club()

    free = await courts.availability.execute(
        CourtAvailabilityQuery(
            club_id=club.id, category_id=category.id, window=EVENING
        )
    )
    assert set(free) == set(court_ids)

    await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=ClubHeld(),
        )
    )

    after = await courts.availability.execute(
        CourtAvailabilityQuery(
            club_id=club.id, category_id=category.id, window=EVENING
        )
    )
    assert len(after) == 2


async def test_no_stored_column_answers_how_many_are_free(courts, session_factory):
    """The projection has nothing to drift from, and this is where that stops
    being a claim in a docstring."""

    columns = {column.name for column in ReservationORM.__table__.columns}
    columns |= {column.name for column in BookingORM.__table__.columns}

    assert not {c for c in columns if "avail" in c or "remaining" in c}


async def test_releasing_gives_the_court_back(courts):
    club, category, _ = await courts.a_club(courts=1)
    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )

    await courts.release.execute(
        ReleaseReservationCommand(reservation_id=reservation.id)
    )

    free = await courts.availability.execute(
        CourtAvailabilityQuery(
            club_id=club.id, category_id=category.id, window=EVENING
        )
    )
    assert len(free) == 1


async def test_a_released_claim_keeps_its_row_and_its_history(
    courts, session_factory
):
    """*"A court's booking history is a query over reservations"* — which is
    false the moment a row can vanish."""

    club, category, _ = await courts.a_club(courts=1)
    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )
    court = reservation.court_id

    await courts.release.execute(
        ReleaseReservationCommand(reservation_id=reservation.id)
    )
    await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=ClubHeld(),
        )
    )

    history = await courts.history.execute(court)
    assert len(history) == 2
    assert [r.is_live for r in history] == [False, True]
    assert await count(session_factory, ReservationORM) == 2


async def test_releasing_an_unknown_reservation_is_a_refusal(courts):
    with pytest.raises(ReservationNotFound):
        await courts.release.execute(
            ReleaseReservationCommand(reservation_id=uuid.uuid4())
        )


# --- reassignment -----------------------------------------------------------


async def test_reassignment_within_a_category_changes_the_court_and_nothing_else(
    courts,
):
    club, category, court_ids = await courts.a_club()
    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )
    elsewhere = next(c for c in court_ids if c != reservation.court_id)

    moved = await courts.reassign.execute(
        ReassignCourtCommand(reservation_id=reservation.id, court_id=elsewhere)
    )

    stored = await courts.reservations.get(reservation.id)
    assert moved.court_id == elsewhere == stored.court_id
    assert stored.category_id == category.id
    assert stored.played == EVENING
    assert stored.version == 1


async def test_reassigning_into_another_category_is_refused(courts):
    club, category, _ = await courts.a_club()
    other = await courts.add_category.execute(
        AddCourtCategoryCommand(
            club_id=club.id,
            name=CategoryName("Tennis · clay, outdoor"),
            sport=Sport.TENNIS,
            rate=zloty(80),
        )
    )
    outside = await courts.add_court.execute(
        AddCourtCommand(
            club_id=club.id, category_id=other.id, label=CourtLabel("Clay 1")
        )
    )
    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )

    with pytest.raises(CourtNotInCategory):
        await courts.reassign.execute(
            ReassignCourtCommand(reservation_id=reservation.id, court_id=outside.id)
        )


async def test_reassigning_onto_a_retired_court_is_refused(courts):
    club, category, court_ids = await courts.a_club()
    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )
    elsewhere = next(c for c in court_ids if c != reservation.court_id)
    await courts.retire_court.execute(
        RetireCourtCommand(club_id=club.id, court_id=elsewhere)
    )

    with pytest.raises(CourtNotInCategory):
        await courts.reassign.execute(
            ReassignCourtCommand(reservation_id=reservation.id, court_id=elsewhere)
        )


async def test_reassigning_an_unknown_reservation_is_a_refusal(courts):
    with pytest.raises(ReservationNotFound):
        await courts.reassign.execute(
            ReassignCourtCommand(
                reservation_id=uuid.uuid4(), court_id=uuid.uuid4()
            )
        )


async def test_a_stale_writer_is_refused_and_never_merged(courts):
    club, category, court_ids = await courts.a_club()
    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )
    stale = await courts.reservations.get(reservation.id)
    elsewhere = next(c for c in court_ids if c != reservation.court_id)

    await courts.reassign.execute(
        ReassignCourtCommand(reservation_id=reservation.id, court_id=elsewhere)
    )

    stale.release(at=at(12))
    with pytest.raises(ConcurrentReservationModification):
        await courts.reservations.save(stale)


# --- a booking holds a reservation -----------------------------------------


async def test_booking_writes_a_booking_and_the_claim_it_holds(
    courts, session_factory
):
    club, category, court_ids = await courts.a_club()
    player = uuid.uuid4()

    booking = await courts.book.execute(
        BookCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            player_id=player,
        )
    )

    reservation = await courts.reservations.get(booking.reservation_id)
    assert reservation is not None
    assert reservation.court_id in court_ids
    assert reservation.kind is HolderKind.BOOKING
    assert reservation.holder.booking_id == booking.id
    assert await count(session_factory, BookingORM) == 1
    assert await count(session_factory, ReservationORM) == 1


async def test_the_booking_price_is_the_category_rate_through_the_clubs_multipliers(
    courts,
):
    club, category, _ = await courts.a_club()

    booking = await courts.book.execute(
        BookCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            player_id=uuid.uuid4(),
        )
    )

    assert int(booking.price) == int(zloty(120))


async def test_reassigning_the_court_leaves_the_quoted_price_alone(courts):
    """*"The exact court is assigned, never chosen — and the price cannot
    change."* Structural: the price is on the booking, the court is on the
    reservation, and the two writes do not meet."""

    club, category, court_ids = await courts.a_club()
    booking = await courts.book.execute(
        BookCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            player_id=uuid.uuid4(),
        )
    )
    reservation = await courts.reservations.get(booking.reservation_id)
    elsewhere = next(c for c in court_ids if c != reservation.court_id)

    await courts.reassign.execute(
        ReassignCourtCommand(reservation_id=reservation.id, court_id=elsewhere)
    )

    after = await courts.bookings.get(booking.id)
    assert int(after.price) == int(booking.price)
    moved = await courts.reservations.get(reservation.id)
    assert moved.category_id == category.id
    assert moved.published(now=at(17, 45)).category_id == category.id


async def test_a_booking_is_found_from_the_reservation_it_holds(courts):
    club, category, _ = await courts.a_club()
    booking = await courts.book.execute(
        BookCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            player_id=uuid.uuid4(),
        )
    )

    assert (await courts.bookings.for_reservation(booking.reservation_id)).id == (
        booking.id
    )


async def test_a_match_hold_has_no_booking(courts):
    """The other side of *a Booking holds a Reservation and is not one*."""

    club, category, _ = await courts.a_club()
    reservation = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )

    assert await courts.bookings.for_reservation(reservation.id) is None


async def test_a_booking_that_cannot_get_a_court_writes_neither_row(
    courts, session_factory
):
    """One transaction. A booking whose reservation failed is a player who has
    bought nothing and been told otherwise."""

    club, category, _ = await courts.a_club(courts=1)
    await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=ClubHeld(),
        )
    )

    with pytest.raises(InventoryLost):
        await courts.book.execute(
            BookCourtCommand(
                club_id=club.id,
                category_id=category.id,
                played=EVENING,
                player_id=uuid.uuid4(),
            )
        )

    assert await count(session_factory, BookingORM) == 0
    assert await count(session_factory, ReservationORM) == 1


# --- losing the race, without a database that can produce one ---------------


class _RefusesOnce:
    """A reservation repository that loses the first *n* claims it is given.

    The stand-in is for **losing**, not for the constraint: the use case's job
    on a refusal has no database in it, and this is where that job is asserted.
    The constraint itself is `tests/integration/test_reservation_exclusion.py`.
    """

    def __init__(self, real, refusals: int) -> None:
        self._real = real
        self._left = refusals
        self.refused: list = []

    async def get(self, reservation_id):
        return await self._real.get(reservation_id)

    async def overlapping(self, *, court_ids, window):
        return await self._real.overlapping(court_ids=court_ids, window=window)

    async def for_court(self, court_id):
        return await self._real.for_court(court_id)

    async def add(self, reservation: Reservation):
        if self._left:
            self._left -= 1
            self.refused.append(reservation.court_id)
            raise CourtAlreadyClaimed()
        return await self._real.add(reservation)

    async def save(self, reservation):
        return await self._real.save(reservation)


async def test_a_refused_claim_is_re_asked_and_lands_on_another_court(
    session_factory, clock
):
    """*"One winner and one query result"* — the loser gets a court, not an
    error, and the player never hears the word *race*."""

    async with session_factory() as session:
        courts = _Courts(session, clock)
        club, category, court_ids = await courts.a_club(courts=3)
        refusing = _RefusesOnce(courts.reservations, refusals=1)
        claim = ClaimCourt(courts.clubs, refusing, build_unit_of_work(session))

        reservation = await claim.execute(
            ClaimCourtCommand(
                club_id=club.id,
                category_id=category.id,
                played=EVENING,
                holder=MatchHeld(uuid.uuid4()),
            )
        )

    assert len(refusing.refused) == 1
    assert reservation.court_id in court_ids
    assert reservation.court_id != refusing.refused[0]


async def test_a_court_that_refuses_is_not_offered_again_in_the_same_ask(
    session_factory, clock
):
    """The loop is bounded by the courts, not by an attempt count.

    Re-scanning alone would hand back the same court for ever: the writer that
    beat us may not have committed, so nothing in the database says it is taken.
    """

    async with session_factory() as session:
        courts = _Courts(session, clock)
        club, category, court_ids = await courts.a_club(courts=3)
        refusing = _RefusesOnce(courts.reservations, refusals=3)
        claim = ClaimCourt(courts.clubs, refusing, build_unit_of_work(session))

        with pytest.raises(InventoryLost):
            await claim.execute(
                ClaimCourtCommand(
                    club_id=club.id,
                    category_id=category.id,
                    played=EVENING,
                    holder=MatchHeld(uuid.uuid4()),
                )
            )

    assert sorted(refusing.refused, key=str) == sorted(court_ids, key=str)


async def test_every_court_refusing_becomes_the_one_story_a_player_hears(
    session_factory, clock
):
    """`CourtAlreadyClaimed` never reaches a caller outside this context."""

    async with session_factory() as session:
        courts = _Courts(session, clock)
        club, category, _ = await courts.a_club(courts=2)
        refusing = _RefusesOnce(courts.reservations, refusals=99)
        claim = ClaimCourt(courts.clubs, refusing, build_unit_of_work(session))

        with pytest.raises(InventoryLost):
            await claim.execute(
                ClaimCourtCommand(
                    club_id=club.id,
                    category_id=category.id,
                    played=EVENING,
                    holder=ClubHeld(),
                )
            )


# --- the ordering that rebuilds a court's history ---------------------------


@pytest.fixture
async def descending_uuids(monkeypatch):
    """Mint reservation ids counting **down**, so every later row sorts first.

    `new_uuid` is `uuid4`, so which of two rows sharing a claimed start came
    back first was a coin flip decided when they were written. A descending
    counter takes the losing side of that flip every time, which turns a test
    that would fail half the runs into one that fails all of them — the lesson
    `tests/unit/test_club_repository.py` paid for one context over.

    Patched in the *use case's* namespace, because that is where `new_uuid` is
    bound: a reservation's id is minted by `ClaimCourt`, not by the adapter.
    """

    from app.modules.courts.application import claim_court as claim_court_module

    remaining = iter(range(2**32, 0, -1))
    monkeypatch.setattr(
        claim_court_module, "new_uuid", lambda: uuid.UUID(int=next(remaining))
    )
    # And nowhere else: unlike the club repository, which mints a row id per
    # series version, this adapter mints nothing at all. If that changes, this
    # fixture stops covering the ids that matter and says so here.
    assert not hasattr(reservation_repository_module, "new_uuid")


async def test_a_courts_history_is_ordered_even_when_two_rows_share_an_instant(
    courts, descending_uuids, session_factory
):
    """A released claim and the claim that replaced it share a claimed start.

    Ordering broke that tie on `id`, which is random — so a court's history came
    back either way round, and *what happened to court 3 on Tuesday* had two
    answers. Read back through a **new session**, so this is a re-read from the
    table rather than the identity map handing back what was just written.
    """

    club, category, _ = await courts.a_club(courts=1)
    first = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=MatchHeld(uuid.uuid4()),
        )
    )
    await courts.release.execute(ReleaseReservationCommand(reservation_id=first.id))
    second = await courts.claim.execute(
        ClaimCourtCommand(
            club_id=club.id,
            category_id=category.id,
            played=EVENING,
            holder=ClubHeld(),
        )
    )

    async with session_factory() as session:
        history = await CourtHistory(
            build_reservation_repository(session)
        ).execute(first.court_id)

    assert [r.id for r in history] == [first.id, second.id]
    assert [r.is_live for r in history] == [False, True]
