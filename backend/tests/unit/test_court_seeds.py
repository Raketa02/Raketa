"""The seeded court claims: named for a state, and the name is checked.

Same three claims the two catalogs beside it make, one context over.

1. **The catalog is coherent before a session is opened** — every claim names a
   club and a category that exist, and a booking names a buyer.
2. **The run is idempotent**, and the second run creates nothing.
3. **A name that no longer matches its state stops the run**, checked against the
   *stored* reservation on every run, including one that created nothing.

Plus the one this context adds: **no seeded claim is match-held**, because
Matches has no aggregate and a uuid standing in for one is the scope creep a
walk over imports cannot see.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from sqlalchemy import func, select

from app.bootstrap.composition import build_reservation_repository
from app.seeds.clubs import CLUBS
from app.seeds.courts import (
    RESERVATIONS,
    HolderKind,
    ReservationClaim,
    SeedReservation,
    seed_slot,
)
from app.seeds.catalog import ACCOUNTS
from app.seeds.runner import seed
from app.modules.courts.infrastructure.sqlalchemy_court_models import (
    BookingORM,
    ReservationORM,
)
from app.seeds.runner import SeedFailed


def _only_the_court_catalog(monkeypatch, reservations) -> None:
    monkeypatch.setattr("app.seeds.runner.RESERVATIONS", reservations)


async def count(session_factory, model):
    async with session_factory() as session:
        return (
            await session.execute(select(func.count()).select_from(model))
        ).scalar_one()


# --- 1. the catalog is coherent before anything is written ------------------


def test_every_slug_is_distinct():
    assert len({r.slug for r in RESERVATIONS}) == len(RESERVATIONS)


def test_every_claim_names_a_club_the_club_catalog_holds():
    slugs = {club.slug for club in CLUBS}

    for reservation in RESERVATIONS:
        assert reservation.club_slug in slugs, reservation.slug


def test_every_claim_names_a_category_that_club_has():
    categories = {
        (club.slug, category.name) for club in CLUBS for category in club.categories
    }

    for reservation in RESERVATIONS:
        assert (reservation.club_slug, reservation.category) in categories, (
            reservation.slug
        )


def test_every_booking_names_an_account_the_account_catalog_holds():
    slugs = {account.slug for account in ACCOUNTS}

    for reservation in RESERVATIONS:
        if reservation.held_by is HolderKind.BOOKING:
            assert reservation.player_slug in slugs, reservation.slug


def test_no_seeded_claim_is_match_held():
    """A match hold is granted by the ladder (`Raketa02/Raketa#71`), and seeding
    one here would decide what the ladder decides — leaving a seeded match with
    a `heldSince` nobody derived. Matches has had an aggregate since `#66`; the
    catalog still refuses this at construction, for the later reason."""

    for reservation in RESERVATIONS:
        assert reservation.held_by is not HolderKind.MATCH

    with pytest.raises(ValueError, match="the hold ladder"):
        replace(RESERVATIONS[0], held_by=HolderKind.MATCH)


def test_a_booking_without_a_buyer_is_refused():
    with pytest.raises(ValueError, match="a booking names a buyer"):
        replace(
            RESERVATIONS[0], held_by=HolderKind.BOOKING, player_slug=None
        )


def test_a_club_block_with_a_buyer_is_refused():
    with pytest.raises(ValueError, match="a booking names a buyer"):
        replace(
            RESERVATIONS[0],
            held_by=HolderKind.CLUB,
            player_slug="brand-new-player",
        )


def test_the_windows_are_absolute_and_not_relative_to_now():
    """A seed run is idempotent, and *"next Tuesday at 18:00"* computed at run
    time is a different Tuesday tomorrow — so a second run would claim a second
    court and the run that creates nothing could never happen."""

    assert seed_slot(18) == seed_slot(18)
    for reservation in RESERVATIONS:
        assert reservation.played.start.year == 2026
        assert reservation.played.start == seed_slot(
            reservation.played.start.hour,
            day_offset=reservation.played.start.day - 7,
            length=int(reservation.played.duration),
        ).start


def test_no_two_claims_at_one_club_share_a_window_on_one_category():
    """Two seeded claims that overlapped on one category would be a catalog the
    exclusion constraint refuses — which is the system working, and a seed run
    that cannot finish."""

    seen = set()
    for reservation in RESERVATIONS:
        key = (reservation.club_slug, reservation.category, reservation.played)
        assert key not in seen, reservation.slug
        seen.add(key)


# --- 2. the run, and the run that creates nothing ---------------------------


async def test_the_catalog_is_written_and_a_second_run_writes_nothing(
    session_factory,
):
    async with session_factory() as session:
        first = (await seed(session)).reservations

    assert len(first) == len(RESERVATIONS)
    assert all(entry.created for entry in first)
    written = await count(session_factory, ReservationORM)

    async with session_factory() as session:
        second = (await seed(session)).reservations

    assert not any(entry.created for entry in second)
    assert [entry.reservation_id for entry in second] == [
        entry.reservation_id for entry in first
    ]
    assert await count(session_factory, ReservationORM) == written


async def test_a_booking_is_written_beside_the_claim_it_holds(session_factory):
    async with session_factory() as session:
        seeded = (await seed(session)).reservations

    bookings = [
        entry
        for entry in seeded
        if entry.reservation.held_by is HolderKind.BOOKING
    ]
    assert bookings
    assert await count(session_factory, BookingORM) == len(bookings)


async def test_the_released_claim_keeps_its_row_and_frees_its_court(
    session_factory,
):
    async with session_factory() as session:
        seeded = (await seed(session)).reservations

    given_back = next(
        entry for entry in seeded if entry.reservation.released
    )
    async with session_factory() as session:
        stored = await build_reservation_repository(session).get(
            given_back.reservation_id
        )

    assert stored is not None
    assert not stored.is_live


async def test_the_turnaround_club_claims_more_than_it_plays(session_factory):
    """The reason a club named for its turnaround is in the catalog at all."""

    async with session_factory() as session:
        seeded = (await seed(session)).reservations

    padded = next(
        entry
        for entry in seeded
        if entry.reservation.slug == "court-claimed-past-the-game"
    )
    async with session_factory() as session:
        stored = await build_reservation_repository(session).get(
            padded.reservation_id
        )

    assert stored.claimed.end > stored.played.end
    assert stored.played == padded.reservation.played


# --- 3. a name that lies ----------------------------------------------------


async def test_a_claim_whose_name_no_longer_matches_stops_the_run(
    session_factory, monkeypatch
):
    lying = replace(
        RESERVATIONS[0],
        claim=ReservationClaim(
            promise="a claim held by a booking", holds=lambda r: False
        ),
    )
    _only_the_court_catalog(monkeypatch, (lying,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="a claim held by a booking"):
            await seed(session)


async def test_the_claim_is_checked_on_a_run_that_creates_nothing(
    session_factory, monkeypatch
):
    """The load-bearing half. A claim seeded last month against a catalog that
    has since had its club's turnaround edited is caught by the next
    `make seed`, not by a developer wondering why a court is not on offer."""

    async with session_factory() as session:
        await seed(session)

    impossible: SeedReservation = replace(
        RESERVATIONS[0],
        claim=ReservationClaim(
            promise="a claim on a court that does not exist", holds=lambda r: False
        ),
    )
    _only_the_court_catalog(monkeypatch, (impossible,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="court that does not exist"):
            await seed(session)


async def test_a_claim_naming_a_club_the_catalog_lost_stops_the_run(
    session_factory, monkeypatch
):
    orphan = replace(RESERVATIONS[0], club_slug="club-that-does-not-exist")
    _only_the_court_catalog(monkeypatch, (orphan,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="club catalog does not hold"):
            await seed(session)


async def test_a_claim_naming_a_category_the_club_does_not_have_stops_the_run(
    session_factory, monkeypatch
):
    orphan = replace(RESERVATIONS[0], category="Curling · sheet 1")
    _only_the_court_catalog(monkeypatch, (orphan,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="that club does not have"):
            await seed(session)


async def test_a_booking_naming_a_player_the_catalog_lost_stops_the_run(
    session_factory, monkeypatch
):
    booking = next(r for r in RESERVATIONS if r.held_by is HolderKind.BOOKING)
    orphan = replace(booking, player_slug="player-who-never-registered")
    _only_the_court_catalog(monkeypatch, (orphan,))

    async with session_factory() as session:
        with pytest.raises(SeedFailed, match="account catalog does not hold"):
            await seed(session)
