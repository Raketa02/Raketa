"""What the club does to a booked game (#547; the mechanics §16.7, §16.9,
§16.16).

**Move** puts the game on another court of its sport at the same hour — the
players read the new number. **Cancel** calls it off with the club's reason:
everybody still in is named, to be refunded in full, and it is on nobody's
record. The desk no longer checks players in (#651); a stored check-in folding
to nothing is ``test_retired_check_in_rows_still_fold.py``'s.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, InvariantViolated, Sport, instant
from app.modules.bookings.domain.booking import (
    BookedCourt,
    Booking,
    BookingState,
    CalledOff,
    CancelReason,
)
from app.modules.bookings.domain.events import (
    BookingConfirmed,
    CancelledByClub,
    CourtMoved,
)
from app.modules.bookings.domain.keeping import Keeping, keeping_of
from app.shared.ids import new_uuid

OLA, KUBA, EWA, TOMEK = (new_uuid() for _ in range(4))
GAME = new_uuid()


def _at(hours: float = 0) -> Instant:
    return instant(
        datetime(2026, 10, 5, 6, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


START = _at(5 * 24)
CUT_OFF = START - timedelta(hours=24)
COURT_1 = BookedCourt(court_id=new_uuid(), name="Court 1")
COURT_3 = BookedCourt(court_id=new_uuid(), name="Court 3")

_OPENINGS: dict[object, BookingConfirmed] = {}


def _booked(**overrides) -> Booking:
    fields = dict(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=COURT_1,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=START,
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=CUT_OFF,
        game_id=GAME,
        at=_at(),
    )
    fields.update(overrides)
    booking = Booking.confirmed(**fields)
    [opening] = booking.pull_events()
    assert isinstance(opening, BookingConfirmed)
    _OPENINGS[booking.booking_id] = opening
    return booking


def _replayed(booking: Booking, events) -> Booking:
    return Booking.from_history([_OPENINGS[booking.booking_id], *events])


# --------------------------------------------------------------------------- #
# Move
# --------------------------------------------------------------------------- #


def test_moving_puts_the_game_on_the_other_court_and_the_players_read_its_name():
    booking = _booked()

    booking.move_to(COURT_3, at=_at(1))

    assert booking.court == COURT_3
    [event] = booking.pull_events()
    assert isinstance(event, CourtMoved)
    assert (event.court_id, event.court_name) == (COURT_3.court_id, "Court 3")
    assert _replayed(booking, [event]).court == COURT_3


def test_a_game_with_a_seat_open_can_be_moved_too():
    booking = _booked()
    booking.leave(KUBA, at=_at(1))

    booking.move_to(COURT_3, at=_at(2))

    assert (booking.court, booking.state) == (COURT_3, BookingState.SEAT_OPEN)


def test_a_game_is_never_moved_onto_its_own_court_once_it_has_started_or_off():
    booking = _booked()
    with pytest.raises(InvariantViolated):
        booking.move_to(COURT_1, at=_at(1))
    with pytest.raises(InvariantViolated):
        booking.move_to(COURT_3, at=START)

    booking.cancel(CancelReason.WEATHER, at=_at(1))
    with pytest.raises(InvariantViolated):
        booking.move_to(COURT_3, at=_at(2))


# --------------------------------------------------------------------------- #
# Cancel
# --------------------------------------------------------------------------- #


def test_the_club_cancels_with_its_reason_and_everybody_still_in_is_named():
    booking = _booked()
    booking.leave(KUBA, at=_at(1))
    left = booking.pull_events()

    booking.cancel(CancelReason.REPAIR, at=_at(2))

    assert booking.state is BookingState.CALLED_OFF
    assert booking.called_off is CalledOff.CANCELLED_BY_THE_CLUB
    assert booking.cancel_reason is CancelReason.REPAIR
    assert booking.open_seats == 0
    [event] = booking.pull_events()
    assert isinstance(event, CancelledByClub)
    assert (event.reason, event.player_ids) == ("REPAIR", (OLA, EWA, TOMEK))
    replayed = _replayed(booking, [*left, event])
    assert replayed.called_off is CalledOff.CANCELLED_BY_THE_CLUB
    assert replayed.cancel_reason is CancelReason.REPAIR


def test_a_game_is_cancelled_only_while_it_will_still_be_played():
    started = _booked()
    with pytest.raises(InvariantViolated):
        started.cancel(CancelReason.OTHER, at=START)

    short = _booked()
    short.leave(KUBA, at=CUT_OFF - timedelta(hours=1))
    # Called off by its cut-off, whether or not the job has recorded it.
    with pytest.raises(InvariantViolated):
        short.cancel(CancelReason.OTHER, at=CUT_OFF + timedelta(minutes=1))


def test_a_cancelled_game_is_on_nobody_s_record():
    booking = _booked()
    booking.leave(KUBA, at=CUT_OFF + timedelta(hours=1))
    booking.cancel(CancelReason.DOUBLE_BOOKING, at=CUT_OFF + timedelta(hours=2))

    for player in (OLA, KUBA, EWA, TOMEK):
        assert keeping_of(booking, player, now=START + timedelta(hours=2)) is None


# --------------------------------------------------------------------------- #
# The record
# --------------------------------------------------------------------------- #


def test_a_game_whose_hour_came_whole_is_kept_by_everybody():
    booking = _booked()

    assert keeping_of(booking, OLA, now=START) == Keeping(at=START)
    assert keeping_of(booking, KUBA, now=START) == Keeping(at=START)
    assert keeping_of(booking, OLA, now=START).kept
