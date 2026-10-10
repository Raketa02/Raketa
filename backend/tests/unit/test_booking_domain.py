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


def test_seats_opening_while_it_waits_take_the_request_back_and_the_others_stay():
    """The request is off, and nobody paid — but the people still In keep their
    places, a seat open where each opener sat: the game stays on their Home as
    *Seat open* (Q106)."""

    booking = _requested()

    withdrawn = booking.withdraw_request((KUBA, TOMEK), at=_at(5))

    assert withdrawn is True
    assert booking.state is BookingState.CALLED_OFF
    assert booking.called_off is CalledOff.SEAT_OPENED
    assert (booking.first_side, booking.second_side) == ((OLA,), (EWA,))
    assert booking.taken_back_at == _at(5)
    events = booking.pull_events()
    assert events[-1] == RequestWithdrawn(
        booking_id=booking.booking_id, player_ids=(KUBA, TOMEK), occurred_at=_at(5)
    )
    replayed = Booking.from_history(events)
    assert (replayed.first_side, replayed.second_side) == ((OLA,), (EWA,))
    assert replayed.taken_back_at == _at(5)


def test_a_request_taken_back_says_who_took_their_own_yes_back():
    """Kuba left; Tomek's week filled with another game. The others are told
    Kuba's name, and never why Tomek's seat opened (Q104)."""

    booking = _requested()

    booking.withdraw_request((KUBA, TOMEK), left=(KUBA,), at=_at(5))

    [_, withdrawn] = booking.pull_events()
    assert isinstance(withdrawn, RequestWithdrawn)
    assert withdrawn.left == (KUBA,)


def test_only_a_player_whose_seat_opened_left_it():
    booking = _requested()

    with pytest.raises(InvariantViolated):
        booking.withdraw_request((KUBA,), left=(TOMEK,), at=_at(5))


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
    assert booking.taken_back_at is None
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


# --------------------------------------------------------------------------- #
# The club's yes waits on one payment (#626; the mechanics Q109, Q112)
# --------------------------------------------------------------------------- #


def test_a_share_refused_at_the_club_s_yes_keeps_the_yes_and_the_court():
    """The booking stays accepted — not waiting for the club, which has
    answered — and its court held while Tomek has until then to pay."""

    booking = _requested()

    booking.await_a_payment((TOMEK,), until=_at(40), at=_at(10))

    assert booking.state is BookingState.WAITING_FOR_A_PAYMENT
    assert booking.is_waiting is False
    assert booking.awaits_a_payment is True
    assert booking.pay_by == _at(40)
    assert booking.payers == (TOMEK,)
    assert booking.players == (OLA, KUBA, EWA, TOMEK)
    assert booking.game_id is None
    replayed = _replayed(booking)
    assert replayed.state is BookingState.WAITING_FOR_A_PAYMENT
    assert (replayed.pay_by, replayed.payers) == (_at(40), (TOMEK,))


def test_a_yes_before_the_cut_off_waits_on_a_card_to_fix():
    """#638: before the cut-off nothing is taken, only held, so the yes waits
    on the player's card to be fixed — *waiting for one player's card* — and
    that ends with the wait, whichever way."""

    fixing = _requested()
    paying = _requested()

    fixing.await_a_payment((TOMEK,), until=_at(40), to_fix_the_card=True, at=_at(10))
    paying.await_a_payment((TOMEK,), until=_at(40), at=_at(10))

    assert (fixing.to_fix_the_card, paying.to_fix_the_card) == (True, False)
    assert _replayed(fixing).to_fix_the_card is True
    fixing.payment_not_in_time((TOMEK,), for_good=False, at=_at(40))
    assert fixing.to_fix_the_card is False


def test_the_payment_in_time_books_it_without_asking_the_club_again():
    booking = _requested()
    booking.await_a_payment((TOMEK,), until=_at(40), at=_at(10))

    booking.accept(game_id=GAME, at=_at(25))

    assert booking.state is BookingState.BOOKED
    assert booking.game_id == GAME
    assert booking.pay_by is None
    assert booking.payers == ()


def test_the_payment_not_in_time_calls_it_off_and_frees_the_court():
    """The players read the game as gone back to filling; the club as called
    off — a player's payment did not come in time."""

    booking = _requested()
    booking.await_a_payment((TOMEK,), until=_at(40), at=_at(10))

    assert booking.payment_not_in_time((TOMEK,), for_good=False, at=_at(40))

    assert booking.state is BookingState.CALLED_OFF
    assert booking.called_off is CalledOff.PAYMENT_NOT_IN_TIME
    assert booking.taken_back is True
    assert booking.taken_back_at == _at(40)
    # Nobody is left off the club's row: that would name whose payment it was.
    assert booking.players == (OLA, KUBA, EWA, TOMEK)
    assert booking.called_off_for_good is False
    assert _replayed(booking).called_off is CalledOff.PAYMENT_NOT_IN_TIME


def test_a_share_refused_past_the_book_by_calls_it_off_at_once_for_good():
    booking = _requested()

    assert booking.payment_not_in_time((TOMEK,), for_good=True, at=_at(10))

    assert booking.called_off is CalledOff.PAYMENT_NOT_IN_TIME
    assert booking.called_off_for_good is True
    assert booking.taken_back is False


def test_full_again_after_the_time_ran_out_the_club_is_asked_again():
    booking = _requested()
    booking.await_a_payment((TOMEK,), until=_at(40), at=_at(10))
    booking.payment_not_in_time((TOMEK,), for_good=False, at=_at(40))

    booking.request_again(
        court=COURT,
        first_side=(OLA, KUBA),
        second_side=(EWA, ANIA),
        cut_off=START - timedelta(hours=24),
        answer_by=_at(90),
        filled_by=ANIA,
        at=_at(60),
    )

    assert booking.state is BookingState.WAITING_FOR_THE_CLUB
    assert booking.called_off is None
    assert booking.pay_by is None


def test_a_seat_opening_while_the_payment_is_awaited_takes_the_request_back():
    booking = _requested()
    booking.await_a_payment((TOMEK,), until=_at(40), at=_at(10))

    assert booking.withdraw_request((KUBA,), left=(KUBA,), at=_at(15))

    assert booking.called_off is CalledOff.SEAT_OPENED
    assert booking.pay_by is None
    # Nothing is awaited of a booking taken back: the proposal keeps the time.
    assert booking.payment_not_in_time((TOMEK,), for_good=False, at=_at(40)) is False


def test_only_a_player_on_it_is_awaited_and_only_while_the_club_has_it():
    with pytest.raises(InvariantViolated):
        _requested().await_a_payment((ANIA,), until=_at(40), at=_at(10))
    booked = _requested()
    booked.accept(game_id=GAME, at=_at(5))
    with pytest.raises(InvariantViolated):
        booked.await_a_payment((TOMEK,), until=_at(40), at=_at(10))
