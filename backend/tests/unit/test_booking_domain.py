"""The Booking aggregate's states (#541, #543; the mechanics §14.1, §16.3,
§16.8): born booked, or born waiting for an On request club and then booked,
refused, timed out or withdrawn — and asked again once the game is full again.
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
    BookingAccepted,
    BookingRefused,
    BookingRequested,
    BookingTimedOut,
    RequestWithdrawn,
)
from app.shared.ids import new_uuid

OLA, KUBA, EWA, TOMEK, ANIA = (new_uuid() for _ in range(5))
GAME = new_uuid()


def _at(minutes: int = 0) -> Instant:
    return instant(
        datetime(2026, 10, 5, 6, tzinfo=timezone.utc) + timedelta(minutes=minutes)
    )


START = _at(5 * 24 * 60)
COURT = BookedCourt(court_id=new_uuid(), name="Court 1")


def _requested(**overrides) -> Booking:
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
        answer_by=_at(30),
        filled_by=None,
        at=_at(),
    )
    fields.update(overrides)
    return Booking.requested(**fields)


def _replayed(booking: Booking) -> Booking:
    return Booking.from_history(booking.pull_events())


def test_a_full_game_at_an_on_request_club_waits_for_the_club_with_its_court_held():
    booking = _requested()

    assert booking.state is BookingState.WAITING_FOR_THE_CLUB
    assert booking.game_id is None
    assert booking.answer_by == _at(30)
    assert booking.court == COURT
    assert booking.players == (OLA, KUBA, EWA, TOMEK)
    [event] = booking.pull_events()
    assert isinstance(event, BookingRequested)
    assert event.filled_by is None


def test_a_request_names_the_player_whose_own_act_put_it_to_the_club():
    """Their yes left no seat open, and they saw *It's a game!*: the four are
    told, and theirs is their own (#622). Asked again, it names whoever's act
    filled it again."""

    booking = _requested(filled_by=TOMEK)
    booking.withdraw_request((KUBA,), at=_at(5))
    booking.request_again(
        court=COURT,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=START - timedelta(hours=12),
        answer_by=_at(70),
        filled_by=KUBA,
        at=_at(40),
    )

    asked, _, asked_again = booking.pull_events()
    assert isinstance(asked, BookingRequested)
    assert isinstance(asked_again, BookingRequested)
    assert (asked.filled_by, asked_again.filled_by) == (TOMEK, KUBA)


def test_accepting_books_it_and_names_the_game_it_opened():
    booking = _requested()

    booking.accept(game_id=GAME, at=_at(10))

    assert booking.state is BookingState.BOOKED
    assert booking.game_id == GAME
    assert booking.booked_at == _at(10)
    events = booking.pull_events()
    assert isinstance(events[-1], BookingAccepted)
    replayed = Booking.from_history(events)
    assert (replayed.state, replayed.game_id) == (BookingState.BOOKED, GAME)
    assert replayed.version == 2


def test_refusing_calls_it_off_with_the_club_s_own_note():
    booking = _requested()

    booking.refuse(reason="The desk sold it", at=_at(10))

    assert booking.state is BookingState.CALLED_OFF
    assert booking.called_off is CalledOff.REFUSED
    assert booking.refusal_reason == "The desk sold it"
    assert booking.game_id is None
    events = booking.pull_events()
    assert isinstance(events[-1], BookingRefused)
    assert Booking.from_history(events).called_off is CalledOff.REFUSED


def test_no_answer_by_the_deadline_calls_it_off():
    booking = _requested()

    booking.time_out(at=_at(30))

    assert booking.called_off is CalledOff.NO_ANSWER
    assert isinstance(booking.pull_events()[-1], BookingTimedOut)


def test_it_cannot_time_out_before_its_answer_is_due():
    booking = _requested()

    with pytest.raises(InvariantViolated):
        booking.time_out(at=_at(29))


def test_seats_opening_while_it_waits_take_the_request_back_from_everybody():
    booking = _requested()

    withdrawn = booking.withdraw_request((KUBA, TOMEK), at=_at(5))

    assert withdrawn is True
    assert booking.called_off is CalledOff.SEAT_OPENED
    # Nobody keeps a seat on it: the people still In are on the game, filling.
    assert booking.players == ()
    events = booking.pull_events()
    assert events[-1] == RequestWithdrawn(
        booking_id=booking.booking_id, player_ids=(KUBA, TOMEK), occurred_at=_at(5)
    )
    assert Booking.from_history(events).players == ()


def test_only_a_player_on_the_request_opens_a_seat_on_it():
    booking = _requested()

    with pytest.raises(InvariantViolated):
        booking.withdraw_request((ANIA,), at=_at(5))


def test_withdrawing_a_request_that_is_not_waiting_records_nothing():
    booking = _requested()
    booking.accept(game_id=GAME, at=_at(5))
    booking.pull_events()

    assert booking.withdraw_request((KUBA,), at=_at(6)) is False
    assert booking.pull_events() == []


def test_full_again_the_same_game_asks_the_club_again_with_whoever_is_in():
    booking = _requested()
    booking.withdraw_request((KUBA,), at=_at(5))
    other_court = BookedCourt(court_id=new_uuid(), name="Court 2")

    booking.request_again(
        court=other_court,
        first_side=(OLA, ANIA),
        second_side=(EWA, TOMEK),
        cut_off=START - timedelta(hours=12),
        answer_by=_at(70),
        filled_by=None,
        at=_at(40),
    )

    assert booking.state is BookingState.WAITING_FOR_THE_CLUB
    assert booking.called_off is None
    assert (booking.court, booking.answer_by) == (other_court, _at(70))
    assert booking.players == (OLA, ANIA, EWA, TOMEK)
    replayed = _replayed(booking)
    assert replayed.state is BookingState.WAITING_FOR_THE_CLUB
    assert replayed.players == (OLA, ANIA, EWA, TOMEK)
    assert replayed.version == 3


def test_a_refused_game_is_never_asked_again():
    booking = _requested()
    booking.refuse(reason=None, at=_at(5))

    with pytest.raises(InvariantViolated):
        booking.request_again(
            court=COURT,
            first_side=(OLA, KUBA),
            second_side=(EWA, TOMEK),
            cut_off=START,
            answer_by=_at(40),
            filled_by=None,
            at=_at(10),
        )


def test_only_a_waiting_request_is_answered():
    booking = _requested()
    booking.refuse(reason=None, at=_at(5))

    with pytest.raises(InvariantViolated):
        booking.accept(game_id=GAME, at=_at(6))


def test_an_answer_is_never_due_after_the_game_starts():
    with pytest.raises(InvariantViolated):
        _requested(answer_by=START + timedelta(minutes=1))


def test_a_booking_born_booked_still_replays_as_booked():
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
        cut_off=START - timedelta(hours=24),
        game_id=GAME,
        at=_at(),
    )

    replayed = _replayed(booking)

    assert replayed.state is BookingState.BOOKED
    assert (replayed.game_id, replayed.answer_by) == (GAME, None)
