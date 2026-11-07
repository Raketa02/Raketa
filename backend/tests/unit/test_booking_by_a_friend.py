"""A friends game is the Booking's second birth (#751; ``docs/adr/0202`` §5–§6;
the friends mechanics §8.2, §9): booked the moment its sender sends it, the
sender In and every other seat **invited** — held for its friend for 24 hours,
never past the cut-off — then accepted, declined or run out. The sender may
call it off before the cut-off.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, InvariantViolated, Sport, instant
from app.modules.bookings.domain.booking import (
    Answer,
    BookedCourt,
    Booking,
    BookingState,
    CalledOff,
    PayMode,
    invited_until,
)
from app.modules.bookings.domain.events import (
    BookedByAFriend,
    CalledOffBySender,
    InvitedSeatAccepted,
    InvitedSeatDeclined,
    InvitedSeatRanOut,
)
from app.shared.ids import new_uuid

TOMEK, EWA, MAGDA, ANIA = (new_uuid() for _ in range(4))
GAME = new_uuid()

#: Monday 19:00 in Kraków.
MONDAY = instant(datetime(2026, 11, 9, 18, tzinfo=timezone.utc))
#: Saturday 10:00, its cut-off Friday 10:00.
SATURDAY = MONDAY + timedelta(days=4, hours=15)
CUT_OFF = SATURDAY - timedelta(hours=24)
COURT = BookedCourt(court_id=new_uuid(), name="Court 3", indoor=True)


def _hours(n: float) -> Instant:
    return instant(MONDAY + timedelta(hours=n))


def _sent(**overrides) -> Booking:
    fields = dict(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=COURT,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=SATURDAY,
        share_grosze=25_00,
        sender=TOMEK,
        first_side=(TOMEK, EWA),
        second_side=(MAGDA, ANIA),
        pay_mode=PayMode.SPLIT_THE_COST,
        cut_off=CUT_OFF,
        game_id=GAME,
        at=MONDAY,
    )
    fields.update(overrides)
    return Booking.booked_by_a_friend(**fields)


def _replayed(booking: Booking) -> Booking:
    return Booking.from_history(booking.pull_events())


def test_a_friends_game_is_born_booked_with_only_its_sender_in():
    booking = _sent()

    assert booking.state is BookingState.BOOKED
    assert booking.is_booked and booking.is_friends_game
    assert (booking.sender, booking.pay_mode) == (TOMEK, PayMode.SPLIT_THE_COST)
    assert booking.players == (TOMEK,)
    assert not booking.is_whole
    assert [(seat.player_id, seat.side) for seat in booking.invited] == [
        (EWA, "A"),
        (MAGDA, "B"),
        (ANIA, "B"),
    ]
    assert {seat.until for seat in booking.invited} == {_hours(24)}
    [event] = booking.pull_events()
    assert isinstance(event, BookedByAFriend)
    assert event.first_side == (TOMEK, EWA)


def test_an_invited_seat_is_no_rescue_and_never_calls_the_game_off():
    booking = _sent()

    assert booking.open_seats == 0
    assert not booking.rescuable_at(_hours(1))
    assert booking.short_from is None
    assert not booking.short_at_the_cut_off(now=CUT_OFF)


def test_a_friends_game_replays_as_it_was_sent():
    replayed = _replayed(_sent())

    assert replayed.is_friends_game
    assert replayed.players == (TOMEK,)
    assert [seat.player_id for seat in replayed.waiting_at(_hours(1))] == [
        EWA,
        MAGDA,
        ANIA,
    ]
    assert replayed.version == 1


def test_the_invitation_runs_a_day_never_past_the_cut_off_or_the_start():
    assert invited_until(MONDAY, cut_off=CUT_OFF, start=SATURDAY) == _hours(24)
    late = CUT_OFF - timedelta(hours=3)
    assert invited_until(late, cut_off=CUT_OFF, start=SATURDAY) == CUT_OFF
    after = CUT_OFF + timedelta(hours=1)
    assert invited_until(after, cut_off=CUT_OFF, start=SATURDAY) == SATURDAY


def test_the_sender_must_sit_on_a_side_and_every_side_be_full():
    with pytest.raises(InvariantViolated):
        _sent(sender=new_uuid())
    with pytest.raises(InvariantViolated):
        _sent(first_side=(TOMEK,))


def test_an_accepted_friend_is_in_on_the_side_the_card_drew():
    booking = _sent()
    booking.pull_events()

    booking.accept(EWA, at=_hours(2))
    booking.accept(MAGDA, at=_hours(20))

    assert booking.first_side == (TOMEK, EWA)
    assert booking.second_side == (MAGDA,)
    assert booking.invitation_of(EWA).answer is Answer.ACCEPTED  # type: ignore[union-attr]
    assert [seat.player_id for seat in booking.waiting_at(_hours(21))] == [ANIA]
    assert [type(event) for event in booking.pull_events()] == [
        InvitedSeatAccepted,
        InvitedSeatAccepted,
    ]


def test_the_last_seat_accepted_makes_the_game_whole():
    booking = _sent()
    for friend in (EWA, MAGDA, ANIA):
        booking.accept(friend, at=_hours(3))

    assert booking.is_whole
    assert booking.waiting_at(_hours(3)) == ()
    history = booking.pull_events()
    assert [
        event.last_seat for event in history if isinstance(event, InvitedSeatAccepted)
    ] == [False, False, True]
    assert Booking.from_history(history).players == (TOMEK, EWA, MAGDA, ANIA)


def test_accepting_is_refused_once_the_clock_ended_or_the_seat_was_answered():
    booking = _sent()
    booking.decline(MAGDA, at=_hours(1))

    with pytest.raises(InvariantViolated):
        booking.accept(EWA, at=_hours(24))
    with pytest.raises(InvariantViolated):
        booking.accept(MAGDA, at=_hours(2))
    with pytest.raises(InvariantViolated):
        booking.accept(new_uuid(), at=_hours(2))


def test_a_decline_is_recorded_once_and_empties_the_seat():
    booking = _sent()
    booking.pull_events()

    assert booking.decline(ANIA, at=_hours(5))
    assert not booking.decline(ANIA, at=_hours(6))

    seat = booking.invitation_of(ANIA)
    assert seat is not None
    assert (seat.answer, seat.answered_at) == (Answer.DECLINED, _hours(5))
    assert booking.players == (TOMEK,)
    [event] = booking.pull_events()
    assert isinstance(event, InvitedSeatDeclined)


def test_silence_runs_out_only_once_the_clock_ended():
    booking = _sent()
    booking.pull_events()

    assert not booking.invited_seat_ran_out(ANIA, at=_hours(23))
    assert [seat.player_id for seat in booking.to_run_out(_hours(24))] == [
        EWA,
        MAGDA,
        ANIA,
    ]
    assert booking.invited_seat_ran_out(ANIA, at=_hours(24))
    assert not booking.invited_seat_ran_out(ANIA, at=_hours(25))

    assert booking.invitation_of(ANIA).answer is Answer.RAN_OUT  # type: ignore[union-attr]
    [event] = booking.pull_events()
    assert isinstance(event, InvitedSeatRanOut)


def test_a_waiting_seat_past_its_clock_reads_as_no_longer_waiting():
    booking = _sent()

    assert booking.waiting_at(_hours(24)) == ()
    assert not booking.decline(EWA, at=_hours(24))


def test_the_sender_calls_it_off_naming_everybody_to_tell():
    booking = _sent()
    booking.accept(EWA, at=_hours(2))
    booking.decline(MAGDA, at=_hours(3))
    booking.pull_events()

    booking.call_off_by_the_sender(at=_hours(40))

    assert booking.state is BookingState.CALLED_OFF
    assert booking.called_off is CalledOff.BY_THE_SENDER
    assert not booking.is_booked
    assert booking.waiting_at(_hours(40)) == ()
    [event] = booking.pull_events()
    assert isinstance(event, CalledOffBySender)
    # Ania's clock ran out at 24 hours, though nothing recorded it.
    assert (event.player_ids, event.invited) == ((TOMEK, EWA), ())


def test_waiting_invitees_are_named_when_the_sender_calls_it_off_early():
    booking = _sent()
    booking.pull_events()

    booking.call_off_by_the_sender(at=_hours(1))

    [event] = booking.pull_events()
    assert isinstance(event, CalledOffBySender)
    assert event.invited == (EWA, MAGDA, ANIA)
    assert _replayed(_sent()).called_off is None


def test_calling_it_off_is_the_senders_before_the_cut_off_only():
    with pytest.raises(InvariantViolated):
        _sent().call_off_by_the_sender(at=CUT_OFF)
    called_off = _sent()
    called_off.call_off_by_the_sender(at=_hours(1))
    with pytest.raises(InvariantViolated):
        called_off.call_off_by_the_sender(at=_hours(2))
    by_a_fill = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=COURT,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=SATURDAY,
        share_grosze=25_00,
        first_side=(TOMEK, EWA),
        second_side=(MAGDA, ANIA),
        cut_off=CUT_OFF,
        game_id=GAME,
        at=MONDAY,
    )
    with pytest.raises(InvariantViolated):
        by_a_fill.call_off_by_the_sender(at=_hours(1))
