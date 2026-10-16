"""Rescues: a seat a leaver left open, taken by somebody else (#545; the
mechanics §10.1, §12.3, §19).

**The seat that opened first is taken first**, on its side — the leavers are
refunded in the order they left. Taking the last open seat makes the game whole
again; until then it is still *seat open*. **A game plays full or not at all**
still holds, read now off the seats still open: a seat that opened before the
cut-off and was taken before it calls nothing off. And the record follows — a
leaver whose seat was taken broke nothing.
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
)
from app.modules.bookings.domain.events import (
    BookingConfirmed,
    NoSaidToTheSeat,
    SeatRescued,
)
from app.modules.bookings.domain.keeping import Broken, Keeping, keeping_of
from app.shared.ids import new_uuid

OLA, KUBA, EWA, TOMEK = (new_uuid() for _ in range(4))
ZOSIA, MAREK = new_uuid(), new_uuid()
GAME = new_uuid()


def _at(hours: float = 0) -> Instant:
    return instant(
        datetime(2026, 10, 5, 6, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


#: Saturday's game, five days out; free to leave until a day before it.
START = _at(5 * 24)
CUT_OFF = START - timedelta(hours=24)
COURT = BookedCourt(court_id=new_uuid(), name="Court 1", indoor=True)


def _booked() -> tuple[Booking, BookingConfirmed]:
    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=COURT,
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
    [opening] = booking.pull_events()
    assert isinstance(opening, BookingConfirmed)
    return booking, opening


def test_a_rescue_takes_the_leaver_s_seat_on_their_side_and_the_game_is_whole():
    booking, _ = _booked()
    booking.leave(KUBA, at=_at(1))

    taken = booking.rescue(ZOSIA, at=_at(2))

    assert taken.player_id == KUBA
    assert booking.state is BookingState.BOOKED
    assert booking.first_side == (OLA, ZOSIA)
    assert booking.open_seats == 0
    assert booking.open_since is None
    [*_, rescued] = booking.pull_events()
    assert isinstance(rescued, SeatRescued)
    assert (rescued.player_id, rescued.side, rescued.replacing) == (ZOSIA, "A", KUBA)


def test_the_seat_that_opened_first_is_taken_first():
    booking, _ = _booked()
    booking.leave(EWA, at=_at(1))
    booking.leave(KUBA, at=_at(2))

    first = booking.rescue(ZOSIA, at=_at(3))

    assert first.player_id == EWA
    assert booking.second_side == (TOMEK, ZOSIA)
    assert booking.state is BookingState.SEAT_OPEN
    assert booking.open_seats == 1
    assert booking.open_since == _at(2)
    assert [left.player_id for left in booking.open_departures] == [KUBA]


def test_open_seats_stay_until_the_cut_off_whatever_their_number():
    booking, _ = _booked()
    for leaver in (OLA, KUBA, EWA):
        booking.leave(leaver, at=_at(1))

    assert booking.open_seats == 3
    assert booking.rescuable_at(CUT_OFF - timedelta(seconds=1))
    assert not booking.rescuable_at(CUT_OFF)


def test_a_seat_left_before_the_cut_off_and_taken_before_it_calls_nothing_off():
    booking, _ = _booked()
    booking.leave(KUBA, at=_at(1))
    booking.rescue(ZOSIA, at=CUT_OFF - timedelta(minutes=5))

    assert booking.short_from is None
    assert not booking.short_at_the_cut_off(now=CUT_OFF)


def test_one_seat_taken_of_two_left_before_the_cut_off_still_leaves_it_short():
    booking, _ = _booked()
    booking.leave(KUBA, at=_at(1))
    booking.leave(EWA, at=_at(2))
    booking.rescue(ZOSIA, at=_at(3))

    assert booking.short_at_the_cut_off(now=CUT_OFF)


def test_a_seat_left_after_the_cut_off_is_offered_until_the_start():
    booking, _ = _booked()
    booking.leave(KUBA, at=CUT_OFF + timedelta(hours=1))

    assert booking.rescuable_at(START - timedelta(seconds=1))
    assert not booking.rescuable_at(START)
    booking.rescue(ZOSIA, at=START - timedelta(minutes=30))
    assert booking.state is BookingState.BOOKED


def test_a_whole_game_and_a_game_called_off_have_no_seat_to_take():
    whole, _ = _booked()
    short, _ = _booked()
    short.leave(KUBA, at=_at(1))
    short.call_off_at_the_cut_off(at=CUT_OFF)

    assert not whole.rescuable_at(_at(1))
    assert not short.rescuable_at(CUT_OFF)
    with pytest.raises(InvariantViolated):
        whole.rescue(ZOSIA, at=_at(1))
    with pytest.raises(InvariantViolated):
        short.rescue(ZOSIA, at=CUT_OFF)


def test_nobody_takes_a_seat_on_a_game_they_are_in_or_left():
    booking, _ = _booked()
    booking.leave(KUBA, at=_at(1))

    with pytest.raises(InvariantViolated):
        booking.rescue(OLA, at=_at(2))
    with pytest.raises(InvariantViolated):
        booking.rescue(KUBA, at=_at(2))
    assert booking.leavers == frozenset({KUBA})


def test_a_rescue_replays_from_the_stream():
    booking, opening = _booked()
    booking.leave(EWA, at=_at(1))
    booking.leave(KUBA, at=_at(2))
    booking.rescue(ZOSIA, at=_at(3))
    booking.rescue(MAREK, at=_at(4))

    replayed = Booking.from_history([opening, *booking.pull_events()])

    assert replayed.state is BookingState.BOOKED
    assert replayed.first_side == (OLA, MAREK)
    assert replayed.second_side == (TOMEK, ZOSIA)
    assert [(left.player_id, left.rescued_by) for left in replayed.departures] == [
        (EWA, ZOSIA),
        (KUBA, MAREK),
    ]
    assert replayed.version == booking.version


def test_a_no_to_a_seat_open_card_is_recorded_once():
    booking, opening = _booked()
    booking.leave(KUBA, at=_at(1))

    assert booking.say_no(ZOSIA, at=_at(2))
    assert not booking.say_no(ZOSIA, at=_at(3))

    events = booking.pull_events()
    assert isinstance(events[-1], NoSaidToTheSeat)
    assert len([e for e in events if isinstance(e, NoSaidToTheSeat)]) == 1
    assert Booking.from_history([opening, *events]).said_no == frozenset({ZOSIA})


# --------------------------------------------------------------------------- #
# The record
# --------------------------------------------------------------------------- #


def test_a_leaver_after_the_cut_off_whose_seat_was_taken_broke_nothing():
    booking, _ = _booked()
    booking.leave(KUBA, at=CUT_OFF + timedelta(hours=1))
    booking.rescue(ZOSIA, at=CUT_OFF + timedelta(hours=2))

    assert keeping_of(booking, KUBA, now=START) is None
    assert keeping_of(booking, ZOSIA, now=START) == Keeping(at=START)


def test_a_leaver_before_the_cut_off_whose_seat_was_taken_is_clean_even_if_called_off():
    """Called off because of somebody else's seat, which is nothing on theirs."""

    booking, _ = _booked()
    booking.leave(KUBA, at=_at(1))
    booking.leave(EWA, at=_at(2))
    booking.rescue(ZOSIA, at=_at(3))
    booking.call_off_at_the_cut_off(at=CUT_OFF)

    assert keeping_of(booking, KUBA, now=CUT_OFF) is None
    assert keeping_of(booking, EWA, now=CUT_OFF) == Keeping(
        at=CUT_OFF, broken=Broken.CALLED_OFF_BY_LEAVING
    )
    assert keeping_of(booking, ZOSIA, now=CUT_OFF) is None
