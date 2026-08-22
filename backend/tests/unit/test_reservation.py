"""What a reservation is: two intervals, one holder, and a court published late.

Four claims, each of which is a different system if it changes.

1. **The claimed interval is derived from the holder**, so Raketa's reservations
   carry the club's turnaround and the club's own blocks do not — and nobody can
   assemble one that disagrees with itself, because `claim` is the only
   constructor and never takes a claimed interval.
2. **The player is shown the played interval**, always. `claimed` is what
   excludes; it is not what anybody is told.
3. **The court is named fifteen minutes before play and not before**, and the
   category is named the whole time. That is what lets a seat price be quoted
   before a court exists and stay fixed when one is assigned.
4. **Released, never deleted**, and a released reservation stops claiming.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.kernel import hours, instant, minutes
from app.modules.courts.domain.errors import ReservationAlreadyReleased
from app.modules.courts.domain.reservation import (
    BookingHeld,
    ClubHeld,
    HolderKind,
    MatchHeld,
    Reservation,
    claimed_interval,
    holder_kind,
    is_platform_created,
)
from app.modules.courts.domain.time_range import TimeRange, span

CLUB = uuid4()
COURT = uuid4()
OTHER_COURT = uuid4()
CATEGORY = uuid4()


def at(hour: int, minute: int = 0):
    return instant(datetime(2026, 9, 1, hour, minute, tzinfo=timezone.utc))


PLAYED = span(at(18), hours(1))
TURNAROUND = minutes(15)


def a_reservation(*, holder=ClubHeld(), turnaround=minutes(0), played=PLAYED):
    return Reservation.claim(
        reservation_id=uuid4(),
        club_id=CLUB,
        court_id=COURT,
        category_id=CATEGORY,
        played=played,
        holder=holder,
        turnaround=turnaround,
    )


# --- 1. the claim is the holder's ------------------------------------------


@pytest.mark.parametrize(
    "holder,kind",
    [
        (BookingHeld(uuid4()), HolderKind.BOOKING),
        (MatchHeld(uuid4()), HolderKind.MATCH),
        (ClubHeld(), HolderKind.CLUB),
    ],
)
def test_every_holder_has_a_kind(holder, kind):
    assert holder_kind(holder) is kind
    assert a_reservation(holder=holder).kind is kind


@pytest.mark.parametrize(
    "holder", [BookingHeld(uuid4()), MatchHeld(uuid4())]
)
def test_a_reservation_raketa_creates_is_widened_by_the_turnaround(holder):
    reservation = a_reservation(holder=holder, turnaround=TURNAROUND)

    assert reservation.played == PLAYED
    assert reservation.claimed == TimeRange(start=at(18), end=at(19, 15))


def test_a_reservation_the_club_publishes_is_never_padded():
    """ADR-0035: a club's own block is *"already padded however that club likes,
    and padding it again double-books the gap."*"""

    reservation = a_reservation(holder=ClubHeld(), turnaround=TURNAROUND)

    assert reservation.claimed == reservation.played == PLAYED


def test_whether_to_pad_is_derived_from_the_holder_and_stored_nowhere():
    """A stored flag would be a second spelling of a fact the holder states."""

    assert is_platform_created(BookingHeld(uuid4()))
    assert is_platform_created(MatchHeld(uuid4()))
    assert not is_platform_created(ClubHeld())

    stored = {field for field in Reservation.__dataclass_fields__}
    assert "padded" not in stored
    assert "origin" not in stored
    assert "turnaround" not in stored


def test_claimed_interval_is_the_one_place_the_rule_is_written():
    assert claimed_interval(PLAYED, ClubHeld(), TURNAROUND) == PLAYED
    assert claimed_interval(PLAYED, MatchHeld(uuid4()), TURNAROUND) == (
        PLAYED.widened_by(TURNAROUND)
    )


def test_a_zero_turnaround_leaves_our_own_claim_alone():
    reservation = a_reservation(holder=MatchHeld(uuid4()), turnaround=minutes(0))
    assert reservation.claimed == reservation.played


def test_a_claim_narrower_than_its_play_cannot_be_constructed():
    """The one shape the constructor cannot produce and a bad row could.

    A claim that does not cover the play it is for is a court sold for an hour
    and held for forty minutes, and the twenty minutes are somebody else's.
    """

    with pytest.raises(ValueError, match="narrower than the play"):
        Reservation(
            id=uuid4(),
            club_id=CLUB,
            court_id=COURT,
            category_id=CATEGORY,
            played=PLAYED,
            claimed=span(at(18), minutes(40)),
            holder=ClubHeld(),
        )


# --- 2 and 3. what a reader is told ----------------------------------------


def test_the_category_is_published_from_the_moment_the_claim_exists():
    reservation = a_reservation()

    published = reservation.published(now=at(9))

    assert published.category_id == CATEGORY
    assert published.court_id is None
    assert not published.names_a_court


@pytest.mark.parametrize("minute", [0, 30, 44])
def test_the_court_is_not_named_more_than_fifteen_minutes_before_play(minute):
    reservation = a_reservation()

    assert reservation.published(now=at(17, minute)).court_id is None


def test_the_court_is_named_from_fifteen_minutes_before_play():
    """`courtAssigned`, and the same fifteen minutes as the door code — one
    constant in the kernel, read by both."""

    reservation = a_reservation()

    assert reservation.published(now=at(17, 45)).court_id == COURT
    assert reservation.published(now=at(18, 30)).court_id == COURT


def test_the_court_is_named_internally_the_whole_time():
    """Which is what makes the exclusion real: the row names a court from the
    instant it is written, whatever a reader is told."""

    reservation = a_reservation()

    assert reservation.court_id == COURT
    assert reservation.published(now=at(9)).court_id is None


# --- reassignment ----------------------------------------------------------


def test_reassignment_moves_the_court_and_nothing_else():
    reservation = a_reservation(holder=MatchHeld(uuid4()), turnaround=TURNAROUND)
    before = (reservation.category_id, reservation.played, reservation.claimed)

    reservation.reassign_to(OTHER_COURT)

    assert reservation.court_id == OTHER_COURT
    assert (reservation.category_id, reservation.played, reservation.claimed) == before


def test_the_published_category_survives_a_reassignment():
    reservation = a_reservation()
    published_before = reservation.published(now=at(17, 45))

    reservation.reassign_to(OTHER_COURT)

    assert reservation.published(now=at(17, 45)).category_id == (
        published_before.category_id
    )
    assert reservation.published(now=at(17, 45)).court_id == OTHER_COURT


# --- 4. released, never deleted --------------------------------------------


def test_a_new_reservation_is_live():
    assert a_reservation().is_live


def test_releasing_keeps_the_row_and_stops_the_claim():
    reservation = a_reservation()

    reservation.release(at=at(12))

    assert not reservation.is_live
    assert reservation.released_at == at(12)
    assert reservation.court_id == COURT
    assert reservation.played == PLAYED


def test_releasing_twice_is_refused_rather_than_ignored():
    """A second release would move the instant a claim ended, which is history
    rewritten rather than recorded."""

    reservation = a_reservation()
    reservation.release(at=at(12))

    with pytest.raises(ReservationAlreadyReleased):
        reservation.release(at=at(13))


def test_a_released_reservation_cannot_be_reassigned():
    reservation = a_reservation()
    reservation.release(at=at(12))

    with pytest.raises(ReservationAlreadyReleased):
        reservation.reassign_to(OTHER_COURT)


def test_the_aggregate_never_moves_its_own_version():
    """The repository compares the version on the way out and bumps it. Two
    counters for one fact is one too many — the same split `Club` makes."""

    reservation = a_reservation()
    reservation.release(at=at(12))

    assert reservation.version == 0
