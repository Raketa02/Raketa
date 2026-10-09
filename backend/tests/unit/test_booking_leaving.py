"""Leaving a booked game, and the cut-off (#544; the mechanics §12.3, §13,
§14.1, §15.4).

A player leaving opens their seat — *seat open* — and the game is still the
others'. **A game plays full or not at all**: a seat that opened before the
club's cut-off and is still open at it calls the game off; a seat that opened
after it leaves the game going ahead short.
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
)
from app.modules.bookings.domain.events import (
    BookingConfirmed,
    CalledOffAtCutOff,
    SeatLeft,
)
from app.modules.bookings.domain.keeping import Keeping, keeping_of
from app.shared.ids import new_uuid

OLA, KUBA, EWA, TOMEK = (new_uuid() for _ in range(4))
GAME = new_uuid()


def _at(hours: float = 0) -> Instant:
    return instant(
        datetime(2026, 10, 5, 6, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


#: Saturday's game, five days out; free to leave until a day before it.
START = _at(5 * 24)
CUT_OFF = START - timedelta(hours=24)
COURT = BookedCourt(court_id=new_uuid(), name="Court 1")


_OPENINGS: dict[object, BookingConfirmed] = {}


def _confirmed_event(booking: Booking) -> BookingConfirmed:
    """The event a booking made here was born with."""

    return _OPENINGS[booking.booking_id]


def _booked(**overrides) -> Booking:
    fields = dict(
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
    fields.update(overrides)
    booking = Booking.confirmed(**fields)
    [opening] = booking.pull_events()
    assert isinstance(opening, BookingConfirmed)
    _OPENINGS[booking.booking_id] = opening
    return booking


def test_leaving_opens_the_leaver_s_seat_and_the_game_is_still_the_others():
    booking = _booked()

    booking.leave(KUBA, at=_at(1))

    assert booking.state is BookingState.SEAT_OPEN
    assert booking.players == (OLA, EWA, TOMEK)
    assert booking.open_seats == 1
    [event] = booking.pull_events()
    assert isinstance(event, SeatLeft)
    assert event.player_id == KUBA


def test_a_seat_left_before_the_cut_off_and_still_open_at_it_leaves_the_game_short():
    booking = _booked()
    booking.leave(KUBA, at=CUT_OFF - timedelta(hours=1))

    assert not booking.short_at_the_cut_off(now=CUT_OFF - timedelta(seconds=1))
    assert booking.short_at_the_cut_off(now=CUT_OFF)


def test_a_seat_left_after_the_cut_off_leaves_the_game_going_ahead_short():
    booking = _booked()
    booking.leave(KUBA, at=CUT_OFF + timedelta(hours=1))

    assert booking.state is BookingState.SEAT_OPEN
    assert not booking.short_at_the_cut_off(now=START)


def test_a_game_that_filled_after_its_cut_off_is_never_short_at_it():
    booking = _booked(at=CUT_OFF + timedelta(hours=2))
    booking.leave(KUBA, at=CUT_OFF + timedelta(hours=3))

    assert not booking.short_at_the_cut_off(now=START)


def test_short_at_the_cut_off_it_is_called_off_and_everybody_still_in_is_named():
    booking = _booked()
    booking.leave(KUBA, at=_at(1))

    booking.call_off_at_the_cut_off(at=CUT_OFF + timedelta(minutes=1))

    assert booking.state is BookingState.CALLED_OFF
    assert booking.called_off is CalledOff.SHORT_AT_THE_CUT_OFF
    assert booking.open_seats == 0
    events = booking.pull_events()
    assert isinstance(events[-1], CalledOffAtCutOff)
    assert events[-1].player_ids == (OLA, EWA, TOMEK)
    replayed = Booking.from_history([_confirmed_event(booking), *events])
    assert replayed.called_off is CalledOff.SHORT_AT_THE_CUT_OFF
    assert replayed.players == (OLA, EWA, TOMEK)


def test_a_game_that_is_not_short_at_its_cut_off_is_never_called_off_by_it():
    booking = _booked()
    booking.leave(KUBA, at=CUT_OFF + timedelta(hours=1))

    with pytest.raises(InvariantViolated):
        booking.call_off_at_the_cut_off(at=CUT_OFF + timedelta(hours=2))


def test_a_game_is_not_called_off_before_its_cut_off():
    booking = _booked()
    booking.leave(KUBA, at=_at(1))

    with pytest.raises(InvariantViolated):
        booking.call_off_at_the_cut_off(at=CUT_OFF - timedelta(minutes=1))


def test_nobody_leaves_a_game_that_has_started_or_a_seat_they_do_not_hold():
    booking = _booked()

    with pytest.raises(InvariantViolated):
        booking.leave(KUBA, at=START)
    booking.leave(KUBA, at=_at(1))
    with pytest.raises(InvariantViolated):
        booking.leave(KUBA, at=_at(2))


# --------------------------------------------------------------------------- #
# The record (§15.4): who kept a booked game, and who broke it
# --------------------------------------------------------------------------- #


def test_everybody_who_played_it_through_kept_it_once_its_hour_came():
    booking = _booked()

    assert keeping_of(booking, OLA, now=START - timedelta(minutes=1)) is None
    assert keeping_of(booking, OLA, now=START) == Keeping(kept=True, at=START)


def test_leaving_before_the_cut_off_is_a_mark_only_when_the_game_is_then_called_off():
    booking = _booked()
    booking.leave(KUBA, at=_at(1))

    assert keeping_of(booking, KUBA, now=CUT_OFF - timedelta(minutes=1)) is None
    assert keeping_of(booking, KUBA, now=CUT_OFF) == Keeping(kept=False, at=CUT_OFF)
    booking.call_off_at_the_cut_off(at=CUT_OFF + timedelta(minutes=1))
    assert keeping_of(booking, KUBA, now=START) == Keeping(kept=False, at=CUT_OFF)


def test_nothing_goes_on_the_record_of_those_who_stayed_in_a_game_called_off():
    booking = _booked()
    booking.leave(KUBA, at=_at(1))
    booking.call_off_at_the_cut_off(at=CUT_OFF)

    assert keeping_of(booking, OLA, now=START) is None


def test_leaving_after_the_cut_off_is_a_mark_when_nobody_takes_the_seat_by_the_start():
    booking = _booked()
    booking.leave(KUBA, at=CUT_OFF + timedelta(hours=1))

    assert keeping_of(booking, KUBA, now=START - timedelta(minutes=1)) is None
    assert keeping_of(booking, KUBA, now=START) == Keeping(kept=False, at=START)
    # Nothing goes on the record of the ones who stayed for a game that
    # started short (the mechanics §14.1).
    assert keeping_of(booking, OLA, now=START) is None


def test_a_game_that_was_never_booked_is_on_nobody_s_record():
    booking = Booking.requested(
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
        answer_by=_at(1),
        filled_by=None,
        at=_at(),
    )
    booking.refuse(reason=None, at=_at(0.5))

    assert keeping_of(booking, OLA, now=START) is None
    assert keeping_of(booking, new_uuid(), now=START) is None
