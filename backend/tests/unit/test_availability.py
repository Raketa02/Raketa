"""Availability is computed, and a released claim frees the court.

ADR-0035 rejected the counter alternative by name — *"counters over overlapping
intervals are `#127` wearing a different hat, the club's own private bookings
have to decrement it too, and a counter kept beside the reservations it
summarises is a second thing to keep true."* This file is the projection that
replaced it, tested where it is pure.

The load-bearing case is the last one: a **club's own block** takes a court out
of availability exactly as one of ours does. That is the property a counter
cannot have without the club console remembering to decrement something.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.kernel import hours, instant, minutes
from app.modules.courts.domain.availability import (
    claimed_courts,
    free_courts,
    pick_court,
)
from app.modules.courts.domain.reservation import (
    BookingHeld,
    ClubHeld,
    MatchHeld,
    Reservation,
)
from app.modules.courts.domain.time_range import span

CLUB = uuid4()
CATEGORY = uuid4()
ONE, TWO, THREE = uuid4(), uuid4(), uuid4()
CATALOGUE = (ONE, TWO, THREE)


def at(hour: int, minute: int = 0):
    return instant(datetime(2026, 9, 1, hour, minute, tzinfo=timezone.utc))


EVENING = span(at(18), hours(1))


def claim(court, *, played=EVENING, holder=ClubHeld(), turnaround=minutes(0)):
    return Reservation.claim(
        reservation_id=uuid4(),
        club_id=CLUB,
        court_id=court,
        category_id=CATEGORY,
        played=played,
        holder=holder,
        turnaround=turnaround,
    )


def test_an_empty_club_has_every_court_free():
    assert free_courts(courts=CATALOGUE, reservations=[], window=EVENING) == CATALOGUE


def test_a_claimed_court_is_not_free():
    taken = [claim(TWO)]

    assert free_courts(courts=CATALOGUE, reservations=taken, window=EVENING) == (
        ONE,
        THREE,
    )
    assert claimed_courts(taken, EVENING) == frozenset({TWO})


def test_a_claim_elsewhere_in_the_day_leaves_the_court_free():
    morning = [claim(TWO, played=span(at(9), hours(1)))]

    assert free_courts(courts=CATALOGUE, reservations=morning, window=EVENING) == (
        CATALOGUE
    )


def test_a_claim_that_only_touches_the_window_leaves_the_court_free():
    """Half-open, the same as everywhere else: 17:00–18:00 does not block 18:00."""

    before = [claim(TWO, played=span(at(17), hours(1)))]

    assert free_courts(courts=CATALOGUE, reservations=before, window=EVENING) == (
        CATALOGUE
    )


def test_a_claim_that_overlaps_by_a_minute_takes_the_court():
    overlapping = [claim(TWO, played=span(at(17), minutes(61)))]

    assert TWO not in free_courts(
        courts=CATALOGUE, reservations=overlapping, window=EVENING
    )


def test_a_turnaround_takes_the_court_for_longer_than_the_game():
    """The whole reason the claimed interval is stored: 18:00–19:00 played with
    a fifteen-minute turnaround blocks a 19:00 start and not a 19:15 one."""

    padded = [claim(TWO, holder=MatchHeld(uuid4()), turnaround=minutes(15))]

    assert TWO not in free_courts(
        courts=CATALOGUE, reservations=padded, window=span(at(19), hours(1))
    )
    assert TWO in free_courts(
        courts=CATALOGUE, reservations=padded, window=span(at(19, 15), hours(1))
    )


def test_a_released_claim_frees_the_court():
    withdrawn = claim(TWO, holder=MatchHeld(uuid4()))
    withdrawn.release(at=at(12))

    assert free_courts(courts=CATALOGUE, reservations=[withdrawn], window=EVENING) == (
        CATALOGUE
    )


def test_the_clubs_own_block_takes_a_court_exactly_as_ours_does():
    """The property a counter could not have: nothing has to remember to
    decrement anything, because the club's block *is* a reservation."""

    ours = claim(ONE, holder=BookingHeld(uuid4()))
    theirs = claim(TWO, holder=ClubHeld())

    assert free_courts(
        courts=CATALOGUE, reservations=[ours, theirs], window=EVENING
    ) == (THREE,)


def test_picking_returns_the_first_free_court_in_catalogue_order():
    """Deterministic, so two identical asks pick the same court — which is what
    makes a lost race legible as *somebody took court 3*."""

    assert pick_court(courts=CATALOGUE, reservations=[], window=EVENING) == ONE
    assert (
        pick_court(courts=CATALOGUE, reservations=[claim(ONE)], window=EVENING) == TWO
    )


def test_picking_from_a_full_club_is_nothing_rather_than_an_error():
    """*"It is a query result, always."* Nothing was free."""

    everything = [claim(court) for court in CATALOGUE]

    assert pick_court(courts=CATALOGUE, reservations=everything, window=EVENING) is None


def test_a_category_with_no_courts_at_all_answers_the_same_way():
    """ADR-0079: *no free court* and *no courts at all* are one answer."""

    assert pick_court(courts=(), reservations=[], window=EVENING) is None
    assert free_courts(courts=(), reservations=[], window=EVENING) == ()
