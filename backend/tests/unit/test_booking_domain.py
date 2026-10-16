"""The Booking aggregate's birth (#541; the mechanics §14.1): born booked, at
every club — no club confirms a game (``docs/adr/0196`` §1) — with its court,
its sides, its cut-off and the Game it opened.
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
from app.modules.bookings.domain.events import BookingConfirmed
from app.shared.ids import new_uuid

OLA, KUBA, EWA, TOMEK = (new_uuid() for _ in range(4))
GAME = new_uuid()


def _at(minutes: int = 0) -> Instant:
    return instant(
        datetime(2026, 10, 5, 6, tzinfo=timezone.utc) + timedelta(minutes=minutes)
    )


START = _at(5 * 24 * 60)
COURT = BookedCourt(court_id=new_uuid(), name="Court 1", indoor=True)


def _confirmed(**overrides) -> Booking:
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
        cut_off=START - timedelta(hours=24),
        game_id=GAME,
        at=_at(),
    )
    fields.update(overrides)
    return Booking.confirmed(**fields)


def _replayed(booking: Booking) -> Booking:
    return Booking.from_history(booking.pull_events())


def test_a_full_game_is_born_booked_on_its_court_with_its_game():
    booking = _confirmed()

    assert booking.state is BookingState.BOOKED
    assert booking.is_booked
    assert (booking.court, booking.game_id) == (COURT, GAME)
    assert booking.booked_at == _at()
    assert booking.players == (OLA, KUBA, EWA, TOMEK)
    assert booking.called_off is None
    [event] = booking.pull_events()
    assert isinstance(event, BookingConfirmed)


def test_a_booking_born_booked_replays_as_booked():
    replayed = _replayed(_confirmed())

    assert replayed.state is BookingState.BOOKED
    assert (replayed.game_id, replayed.booked_at) == (GAME, _at())
    assert replayed.version == 1


def test_a_booking_stream_opens_only_with_its_booking():
    booking = _confirmed()
    booking.pull_events()
    booking.leave(KUBA, at=_at(5))
    [left] = booking.pull_events()

    with pytest.raises(TypeError):
        Booking.from_history([left])


def test_every_seat_is_on_a_side_and_nobody_on_both():
    with pytest.raises(InvariantViolated):
        _confirmed(second_side=(EWA,))
    with pytest.raises(InvariantViolated):
        _confirmed(second_side=(OLA, TOMEK))


def test_its_cut_off_is_never_after_the_game():
    with pytest.raises(InvariantViolated):
        _confirmed(cut_off=START + timedelta(minutes=1))
