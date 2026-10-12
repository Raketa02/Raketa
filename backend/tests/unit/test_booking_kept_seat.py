"""A seat kept for a refused rescuer (#640; the mechanics §10.1, Q113).

A rescuer whose share was refused keeps a seat for themselves alone — their
time to fix the card before the cut-off, or to pay after it, never past the
start — and it is offered to nobody else meanwhile. **Read off the clock**: a
keep whose time is up keeps nothing, whether or not its running out is
recorded. **Once**: run out, it is never kept for them again on that game. It
is a seat, not a particular one: the seats are still taken in the order they
opened.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, InvariantViolated, Sport, instant
from app.modules.bookings.domain.booking import BookedCourt, Booking, CancelReason
from app.modules.bookings.domain.events import KeptSeatRanOut, SeatKept, SeatRescued
from app.shared.ids import new_uuid

OLA, KUBA, EWA, TOMEK, ZOSIA, MAREK = (new_uuid() for _ in range(6))


def _at(hours: float = 0) -> Instant:
    return instant(
        datetime(2026, 10, 5, 6, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


#: Saturday's game, five days out; free to leave until a day before it.
START = _at(5 * 24)
CUT_OFF = START - timedelta(hours=24)


def _with_seats_open(*leavers) -> Booking:
    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name="Court 1", indoor=True),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=START,
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=CUT_OFF,
        game_id=new_uuid(),
        at=_at(),
    )
    for leaver in leavers:
        booking.leave(leaver, at=_at(1))
    booking.pull_events()
    return booking


def _keep(booking: Booking, player, *, at: Instant, until: Instant | None = None):
    booking.keep_the_seat(
        player,
        until=until or at + timedelta(minutes=30),
        seat_charge_id=new_uuid(),
        reason="DECLINED",
        to_fix_the_card=at < CUT_OFF,
        at=at,
    )


def test_a_seat_kept_for_one_rescuer_is_offered_to_nobody_else_while_it_runs():
    booking = _with_seats_open(KUBA)

    _keep(booking, ZOSIA, at=_at(2))

    assert booking.rescuable_at(_at(2), by=ZOSIA)
    assert not booking.rescuable_at(_at(2), by=MAREK)
    # Off the clock: the moment it is up, anybody may take it.
    assert booking.rescuable_at(_at(2.5), by=MAREK)
    with pytest.raises(InvariantViolated):
        booking.rescue(MAREK, at=_at(2))


def test_a_kept_seat_holds_a_seat_and_the_seats_go_in_the_order_they_opened():
    booking = _with_seats_open(KUBA, EWA)
    _keep(booking, ZOSIA, at=_at(2))

    marek_s = booking.rescue(MAREK, at=_at(2))
    zosia_s = booking.rescue(ZOSIA, at=_at(2.2))

    assert (marek_s.player_id, zosia_s.player_id) == (KUBA, EWA)
    [*_, rescued] = booking.pull_events()
    assert isinstance(rescued, SeatRescued)
    assert booking.kept == {} and booking.open_seats == 0


def test_a_kept_seat_runs_out_once_and_is_never_kept_for_them_again():
    booking = _with_seats_open(KUBA)
    _keep(booking, ZOSIA, at=_at(2))

    assert not booking.kept_seat_ran_out(ZOSIA, at=_at(2.4))
    assert booking.kept_seat_ran_out(ZOSIA, at=_at(2.5))
    assert not booking.kept_seat_ran_out(ZOSIA, at=_at(2.6))

    events = booking.pull_events()
    assert [type(event) for event in events] == [SeatKept, KeptSeatRanOut]
    assert events[-1].to_fix_the_card is True
    assert booking.keeps_ran_out == frozenset({ZOSIA})
    with pytest.raises(InvariantViolated):
        _keep(booking, ZOSIA, at=_at(3))
    # Still theirs to take while it is free.
    assert booking.rescuable_at(_at(3), by=ZOSIA)


def test_refused_again_within_it_they_keep_the_time_they_had():
    booking = _with_seats_open(KUBA)
    _keep(booking, ZOSIA, at=_at(2))
    until = _at(2) + timedelta(minutes=30)

    _keep(booking, ZOSIA, at=_at(2.2), until=until)

    assert booking.kept[ZOSIA].until == until
    with pytest.raises(InvariantViolated):
        _keep(booking, ZOSIA, at=_at(2.3), until=_at(2.3) + timedelta(minutes=30))


def test_a_seat_is_kept_to_fix_never_past_the_cut_off_nor_to_pay_past_the_start():
    booking = _with_seats_open(KUBA)

    with pytest.raises(InvariantViolated):
        _keep(
            booking,
            ZOSIA,
            at=CUT_OFF - timedelta(minutes=10),
            until=CUT_OFF + timedelta(minutes=20),
        )
    with pytest.raises(InvariantViolated):
        _keep(
            booking,
            ZOSIA,
            at=START - timedelta(minutes=10),
            until=START + timedelta(minutes=20),
        )
    _keep(booking, ZOSIA, at=CUT_OFF - timedelta(minutes=10), until=CUT_OFF)
    assert booking.kept[ZOSIA].to_fix_the_card is True


def test_nobody_on_the_game_nor_a_leaver_of_it_has_a_seat_kept():
    booking = _with_seats_open(KUBA)

    for player in (OLA, KUBA):
        with pytest.raises(InvariantViolated):
            _keep(booking, player, at=_at(2))


def test_a_game_cancelled_or_called_off_keeps_no_seat():
    cancelled = _with_seats_open(KUBA)
    _keep(cancelled, ZOSIA, at=_at(2))
    cancelled.cancel(CancelReason.WEATHER, at=_at(2.1))

    short = _with_seats_open(KUBA)
    _keep(short, ZOSIA, at=CUT_OFF - timedelta(minutes=10), until=CUT_OFF)
    short.call_off_at_the_cut_off(at=CUT_OFF)

    assert cancelled.kept == {} and short.kept == {}


def test_a_kept_seat_folds_back_from_its_stream():
    booking = _with_seats_open(KUBA, EWA)
    history = _opening_and_leaves(booking, KUBA, EWA)
    _keep(booking, ZOSIA, at=_at(2))
    _keep(booking, MAREK, at=_at(2))
    booking.kept_seat_ran_out(MAREK, at=_at(2.5))
    history += booking.pull_events()

    folded = Booking.from_history(history)

    # Run out, Marek's keeps nothing — but what was refused is still known.
    assert set(folded.kept) == {ZOSIA, MAREK}
    assert folded.keeps_ran_out == frozenset({MAREK})
    assert folded.seats_kept(at=_at(2.5)) == 0
    assert folded.version == booking.version


def _opening_and_leaves(booking: Booking, *leavers) -> list:
    """A fresh copy of the booking's first events: its opening and its
    leaves, as the store would hand them back."""

    fresh = Booking.confirmed(
        booking_id=booking.booking_id,
        pool_id=booking.pool_id,
        club_id=booking.club_id,
        court=booking.court,
        sport=booking.sport,
        kind=booking.kind,
        start=booking.start,
        share_grosze=booking.share_grosze,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=booking.cut_off,
        game_id=booking.game_id or new_uuid(),
        at=_at(),
    )
    for leaver in leavers:
        fresh.leave(leaver, at=_at(1))
    return fresh.pull_events()
