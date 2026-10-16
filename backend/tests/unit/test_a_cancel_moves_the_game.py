"""Which free court absorbs a club's cancel — a move by cancel (#672; the
mechanics §16.9, Q122; ``docs/adr/0196`` §2).

**A court absorbs the cancel** when it is at the same club, of the same sport,
at the same hour — the free courts read says so — and it is sold at the game's
own share, of the same kind or indoor for an outdoor game, and indoor for a
*weather* cancel. **Of two, the same kind comes first, then indoor; within
that, the club's own order.** The game moves there: the event names the cancel's
reason and the court it left, and nothing else about the booking changes. A
court another game claimed at the index a moment ago answers
``court_just_taken``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.bookings.domain.booking import (
    BookedCourt,
    Booking,
    BookingState,
    CancelReason,
    FreeCourt,
)
from app.modules.bookings.application.at_the_club import CancelTheBooking
from app.modules.bookings.domain.errors import CourtTaken
from app.modules.bookings.domain.events import BookingConfirmed, CourtMoved
from app.modules.proposals.domain.errors import CourtJustTaken
from app.modules.proposals.domain.home import ClubCancelReason
from app.modules.proposals.infrastructure.bookings import BookingsClubBookings
from app.shared.ids import new_uuid

OLA, KUBA, EWA, TOMEK = (new_uuid() for _ in range(4))
SHARE = 40_00


def _at(hours: float = 0) -> Instant:
    return instant(
        datetime(2026, 10, 5, 6, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


START = _at(5 * 24)
COURT_2 = BookedCourt(court_id=new_uuid(), name="Court 2", indoor=True)
COURT_3 = BookedCourt(court_id=new_uuid(), name="Court 3", indoor=True)
COURT_5 = BookedCourt(court_id=new_uuid(), name="Court 5", indoor=True)
OUTDOOR_4 = BookedCourt(court_id=new_uuid(), name="Court 4", indoor=False)
OUTDOOR_6 = BookedCourt(court_id=new_uuid(), name="Court 6", indoor=False)


def _booked(court: BookedCourt = COURT_2) -> Booking:
    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=court,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=START,
        share_grosze=SHARE,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=START - timedelta(hours=24),
        game_id=new_uuid(),
        at=_at(),
    )
    return booking


def _free(*courts: BookedCourt, share: int = SHARE) -> tuple[FreeCourt, ...]:
    return tuple(FreeCourt(court=court, share_grosze=share) for court in courts)


@pytest.mark.parametrize("because", list(CancelReason))
def test_a_free_court_of_the_same_kind_at_the_same_price_absorbs_it(because):
    assert _booked().absorbing_court(_free(COURT_3), because=because) == COURT_3


def test_an_indoor_game_is_never_absorbed_by_an_outdoor_court():
    booking = _booked()

    assert (
        booking.absorbing_court(_free(OUTDOOR_4), because=CancelReason.REPAIR) is None
    )


def test_an_outdoor_game_goes_to_the_same_kind_first_then_indoors():
    booking = _booked(OUTDOOR_4)

    assert (
        booking.absorbing_court(_free(COURT_3, OUTDOOR_6), because=CancelReason.REPAIR)
        == OUTDOOR_6
    )
    assert booking.absorbing_court(_free(COURT_3), because=CancelReason.REPAIR) == (
        COURT_3
    )


def test_within_a_kind_the_club_s_own_order_decides():
    booking = _booked()

    assert (
        booking.absorbing_court(_free(COURT_5, COURT_3), because=CancelReason.OTHER)
        == COURT_5
    )


def test_weather_moves_an_outdoor_game_only_indoors():
    """An outdoor court at the same hour is rained on too."""

    booking = _booked(OUTDOOR_4)

    assert (
        booking.absorbing_court(_free(OUTDOOR_6, COURT_3), because=CancelReason.WEATHER)
        == COURT_3
    )
    assert (
        booking.absorbing_court(_free(OUTDOOR_6), because=CancelReason.WEATHER) is None
    )


def test_a_court_sold_at_another_price_never_absorbs_it():
    booking = _booked()
    dearer = _free(COURT_3, share=SHARE + 5_00)

    assert booking.absorbing_court(dearer, because=CancelReason.REPAIR) is None
    assert (
        booking.absorbing_court((*dearer, *_free(COURT_5)), because=CancelReason.REPAIR)
        == COURT_5
    )


def test_the_game_s_own_court_never_absorbs_it():
    booking = _booked()

    assert booking.absorbing_court(_free(COURT_2), because=CancelReason.REPAIR) is None


def test_a_move_by_cancel_names_the_reason_and_the_court_it_left():
    booking = _booked()
    [opening] = booking.pull_events()
    assert isinstance(opening, BookingConfirmed)

    booking.move_to(COURT_3, at=_at(1), because=CancelReason.REPAIR)

    [event] = booking.pull_events()
    assert isinstance(event, CourtMoved)
    assert (event.court_name, event.indoor, event.reason, event.moved_from) == (
        "Court 3",
        True,
        "REPAIR",
        "Court 2",
    )
    # Nothing else about the booking changes: the same four, booked.
    replayed = Booking.from_history([opening, event])
    assert (replayed.court, replayed.state, replayed.players) == (
        COURT_3,
        BookingState.BOOKED,
        (OLA, KUBA, EWA, TOMEK),
    )


def test_the_club_s_own_move_names_no_reason():
    booking = _booked()
    booking.pull_events()

    booking.move_to(COURT_3, at=_at(1))

    [event] = booking.pull_events()
    assert isinstance(event, CourtMoved)
    assert (event.reason, event.moved_from) == (None, "Court 2")


# --------------------------------------------------------------------------- #
# The race on the court hour's index
# --------------------------------------------------------------------------- #


class _ClaimedAtTheIndex:
    """A booking store whose court hour another game claimed a moment ago:
    the save meets the unique index."""

    def __init__(self, booking: Booking) -> None:
        self._booking = booking

    async def load(self, booking_id):
        return self._booking if booking_id == self._booking.booking_id else None

    async def save(self, booking: Booking) -> None:
        raise CourtTaken()


class _Courts:
    def __init__(self, *free: FreeCourt) -> None:
        self._free = free

    async def free_courts(self, club_id, *, sport, start):
        return self._free


class _NoGames:
    async def call_off_whole(self, booking_id, *, at) -> None:
        raise AssertionError("a move by cancel calls no game off")


class _NoClosures:
    async def close(self, club_id, court_id, *, start, because, at) -> None:
        raise AssertionError("a court is closed only once the booking's save freed it")


async def test_a_court_another_game_claimed_a_moment_ago_is_court_just_taken():
    """The absorbing court read free, and another game's booking took its hour
    before this one's save: the transaction is spent, and the club is answered
    ``court_just_taken`` — pressing again decides afresh."""

    booking = _booked()
    booking.pull_events()
    cancel = CancelTheBooking(
        bookings=_ClaimedAtTheIndex(booking),
        games=_NoGames(),
        courts=_Courts(*_free(COURT_3)),
        closures=_NoClosures(),
    )
    club = BookingsClubBookings(
        bookings=_ClaimedAtTheIndex(booking),
        directory=None,
        move=None,
        cancel=cancel,
    )

    with pytest.raises(CourtJustTaken):
        await club.cancel(
            booking.booking_id,
            because=ClubCancelReason.REPAIR,
            anyway=False,
            at=_at(1),
        )
