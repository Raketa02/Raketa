"""**A friends game's empty seats, and leaving it** (#752; the friends mechanics
§10–§11): a seat nobody holds is the sender's to fill until the cut-off —
another invitation, or *Open to the group* — the first accept or rescue takes
it, and the cut-off opens every seat still empty on a game its sender's card
covers. The sender's leave turns a *Split* game ordinary; with *Whole court*
he keeps paying.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, InvariantViolated, Sport, instant
from app.modules.bookings.domain.booking import (
    COVER_WARNING_BEFORE,
    Answer,
    BookedCourt,
    Booking,
    BookingState,
    Emptied,
    PayMode,
    Vacancy,
)
from app.modules.bookings.domain.events import (
    CoverWarned,
    InvitedSeatAccepted,
    InvitedSeatRanOut,
    InvitedSeatTaken,
    SeatInvited,
    SeatOpened,
)
from app.shared.ids import new_uuid

TOMEK, EWA, MAGDA, ANIA = (new_uuid() for _ in range(4))
PIOTR, KASIA, MAREK, KUBA = (new_uuid() for _ in range(4))
GAME = new_uuid()

#: Monday 19:00 in Kraków.
MONDAY = instant(datetime(2026, 11, 9, 18, tzinfo=timezone.utc))
#: Saturday 10:00, its cut-off Friday 10:00.
SATURDAY = MONDAY + timedelta(days=4, hours=15)
CUT_OFF = SATURDAY - timedelta(hours=24)
#: Wednesday, well before the cut-off.
WEDNESDAY = MONDAY + timedelta(days=2)
COURT = BookedCourt(court_id=new_uuid(), name="Court 3", indoor=True)


def _hours(n: float) -> Instant:
    return instant(MONDAY + timedelta(hours=n))


def _sent(pay_mode: PayMode = PayMode.SPLIT_THE_COST) -> Booking:
    return Booking.booked_by_a_friend(
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
        pay_mode=pay_mode,
        cut_off=CUT_OFF,
        game_id=GAME,
        at=MONDAY,
    )


def _ania_said_no(pay_mode: PayMode = PayMode.SPLIT_THE_COST) -> Booking:
    """Ewa and Magda In, Ania's seat empty: *can't make it*."""

    booking = _sent(pay_mode)
    booking.accept(EWA, at=_hours(1))
    booking.accept(MAGDA, at=_hours(2))
    booking.decline(ANIA, at=_hours(3))
    return booking


def _replayed(booking: Booking) -> Booking:
    return Booking.from_history(booking.pull_events())


def _recorded(booking: Booking) -> list:
    return booking.pull_events()


# --------------------------------------------------------------------------- #
# An empty seat
# --------------------------------------------------------------------------- #


def test_a_seat_its_friend_declined_is_empty_and_no_rescue():
    booking = _ania_said_no()

    assert booking.state is BookingState.BOOKED
    assert booking.open_seats == 0
    assert not booking.rescuable_at(_hours(4))
    [empty] = booking.empty
    assert (empty.seat_of, empty.side, empty.how) == (ANIA, "B", Emptied.DECLINED)
    assert booking.vacancies == (Vacancy(seat_of=ANIA, side="B"),)
    # Nothing happens on its own before the cut-off, and never a call-off.
    assert booking.short_from is None
    assert _replayed(booking).empty == booking.empty


def test_a_seat_whose_friend_did_not_answer_is_empty_from_their_time_s_end():
    booking = _sent()
    until = booking.invited[0].until

    booking.invited_seat_ran_out(EWA, at=until + timedelta(minutes=5))

    [empty] = booking.empty
    assert (empty.seat_of, empty.how, empty.since) == (EWA, Emptied.RAN_OUT, until)


def test_anybody_in_invites_a_friend_of_theirs_into_the_empty_seat():
    booking = _ania_said_no()
    _recorded(booking)

    seat = booking.invite(PIOTR, by=EWA, seat_of=ANIA, at=WEDNESDAY)

    [invited] = _recorded(booking)
    assert isinstance(invited, SeatInvited)
    assert (invited.player_id, invited.invited_by, invited.seat_of) == (
        PIOTR,
        EWA,
        ANIA,
    )
    assert (seat.side, seat.seat, seat.until) == (
        "B",
        ANIA,
        instant(WEDNESDAY + timedelta(hours=24)),
    )
    assert booking.waiting_at(WEDNESDAY) == (seat,)


def test_each_invitation_arrives_when_its_seat_was_invited_into():
    """What *Needs your answer* dates an invitation by (#815): the card's own
    seats at the send, a seat invited into later at that invitation — and an
    answer never moves it."""

    booking = _ania_said_no()
    booking.invite(PIOTR, by=EWA, seat_of=ANIA, at=WEDNESDAY)

    arrivals = {seat.player_id: seat.invited_at for seat in booking.invited}

    assert arrivals == {EWA: MONDAY, MAGDA: MONDAY, ANIA: MONDAY, PIOTR: WEDNESDAY}
    assert {
        seat.player_id: seat.invited_at for seat in _replayed(booking).invited
    } == arrivals


def test_an_invitation_never_runs_past_the_cut_off():
    booking = _ania_said_no()

    seat = booking.invite(
        PIOTR, by=TOMEK, seat_of=ANIA, at=CUT_OFF - timedelta(hours=2)
    )

    assert seat.until == CUT_OFF


@pytest.mark.parametrize(
    "who, by, seat_of",
    [
        # Not In.
        (PIOTR, ANIA, ANIA),
        # No such empty seat.
        (PIOTR, TOMEK, MAGDA),
        # Already on the game.
        (EWA, TOMEK, ANIA),
        # Invited to it once already.
        (ANIA, TOMEK, ANIA),
    ],
)
def test_an_invitation_into_no_empty_seat_by_somebody_in_is_refused(who, by, seat_of):
    booking = _ania_said_no()

    with pytest.raises(InvariantViolated):
        booking.invite(who, by=by, seat_of=seat_of, at=WEDNESDAY)


def test_the_first_accept_takes_the_seat_and_the_other_invitation_ends_taken():
    booking = _ania_said_no()
    booking.invite(PIOTR, by=TOMEK, seat_of=ANIA, at=WEDNESDAY)
    booking.invite(KASIA, by=EWA, seat_of=ANIA, at=WEDNESDAY + timedelta(hours=1))
    _recorded(booking)

    booking.accept(KASIA, at=WEDNESDAY + timedelta(hours=2))

    accepted, ended = _recorded(booking)
    assert isinstance(accepted, InvitedSeatAccepted)
    assert (accepted.side, accepted.last_seat) == ("B", True)
    assert isinstance(ended, InvitedSeatTaken)
    assert (ended.player_id, ended.taken_by) == (PIOTR, KASIA)
    assert booking.is_whole and booking.empty == ()
    assert booking.second_side == (MAGDA, KASIA)
    assert booking.invitation_of(PIOTR).answer is Answer.TAKEN
    with pytest.raises(InvariantViolated):
        booking.accept(PIOTR, at=WEDNESDAY + timedelta(hours=3))


def test_a_seat_invitation_declined_leaves_the_seat_empty_as_it_was():
    booking = _ania_said_no()
    booking.invite(PIOTR, by=TOMEK, seat_of=ANIA, at=WEDNESDAY)

    booking.decline(PIOTR, at=WEDNESDAY + timedelta(hours=1))

    assert [seat.seat_of for seat in booking.empty] == [ANIA]
    # The seat is named by the friend last invited into it.
    assert booking.unpaid_seats(now=WEDNESDAY) == (PIOTR,)


# --------------------------------------------------------------------------- #
# Open to the group
# --------------------------------------------------------------------------- #


def test_the_sender_opens_the_seat_to_the_group_as_a_covered_rescue():
    booking = _ania_said_no()
    _recorded(booking)

    booking.open_to_the_group(ANIA, at=WEDNESDAY)

    [opened] = _recorded(booking)
    assert isinstance(opened, SeatOpened) and not opened.at_the_cut_off
    assert booking.state is BookingState.SEAT_OPEN
    assert booking.open_seats == 1
    [left] = booking.open_departures
    assert (left.player_id, left.side, left.covered) == (ANIA, "B", True)
    assert booking.rescuable_at(WEDNESDAY)
    # Covered: still open at the cut-off, it calls nothing off.
    assert booking.short_from is None
    assert not booking.short_at_the_cut_off(now=CUT_OFF)
    assert booking.rescuable_at(CUT_OFF + timedelta(hours=3))


def test_only_an_empty_seat_opens_and_only_before_the_cut_off():
    booking = _ania_said_no()

    with pytest.raises(InvariantViolated):
        booking.open_to_the_group(MAGDA, at=WEDNESDAY)
    with pytest.raises(InvariantViolated):
        booking.open_to_the_group(ANIA, at=CUT_OFF)


def test_a_rescue_takes_the_opened_seat_and_ends_every_invitation_into_it():
    booking = _ania_said_no()
    booking.invite(PIOTR, by=TOMEK, seat_of=ANIA, at=WEDNESDAY)
    booking.open_to_the_group(ANIA, at=WEDNESDAY + timedelta(hours=1))
    _recorded(booking)

    taken = booking.rescue(MAREK, at=WEDNESDAY + timedelta(hours=2))

    assert (taken.player_id, taken.covered) == (ANIA, True)
    rescued, ended = _recorded(booking)
    assert isinstance(ended, InvitedSeatTaken)
    assert (ended.player_id, ended.taken_by) == (PIOTR, MAREK)
    assert booking.state is BookingState.BOOKED and booking.is_whole


def test_a_friend_invited_into_an_opened_seat_takes_it_first():
    booking = _ania_said_no()
    booking.open_to_the_group(ANIA, at=WEDNESDAY)
    booking.invite(PIOTR, by=MAGDA, seat_of=ANIA, at=WEDNESDAY + timedelta(hours=1))

    booking.accept(PIOTR, at=WEDNESDAY + timedelta(hours=2))

    [taken] = booking.departures
    assert (taken.rescued_by, taken.covered) == (PIOTR, True)
    assert booking.state is BookingState.BOOKED and booking.is_whole
    assert not booking.rescuable_at(WEDNESDAY + timedelta(hours=2))
    assert _replayed(booking).departures == booking.departures


# --------------------------------------------------------------------------- #
# At the cut-off
# --------------------------------------------------------------------------- #


def test_at_the_cut_off_every_seat_still_empty_opens_to_the_group():
    booking = _ania_said_no()
    _recorded(booking)

    opened = booking.open_at_the_cut_off(at=CUT_OFF)

    assert opened == (ANIA,)
    [event] = _recorded(booking)
    assert isinstance(event, SeatOpened) and event.at_the_cut_off
    [left] = booking.open_departures
    assert left.covered and left.at == CUT_OFF
    assert not booking.short_at_the_cut_off(now=CUT_OFF)
    # Offered until the start.
    assert booking.rescuable_at(SATURDAY - timedelta(minutes=1))
    assert booking.open_at_the_cut_off(at=CUT_OFF + timedelta(minutes=1)) == ()


def test_the_cut_off_runs_out_an_invitation_first_then_opens_its_seat():
    booking = _sent()
    booking.accept(EWA, at=_hours(1))
    booking.accept(MAGDA, at=_hours(2))
    _recorded(booking)

    opened = booking.open_at_the_cut_off(at=CUT_OFF)

    assert opened == (ANIA,)
    ran_out, open_ = _recorded(booking)
    assert isinstance(ran_out, InvitedSeatRanOut)
    assert isinstance(open_, SeatOpened)


def test_nothing_opens_before_the_cut_off():
    booking = _ania_said_no()

    assert booking.open_at_the_cut_off(at=CUT_OFF - timedelta(seconds=1)) == ()
    assert booking.empty != ()


def test_a_seat_emptied_after_the_cut_off_is_a_rescue_at_once():
    booking = _sent()
    booking.accept(EWA, at=_hours(1))
    booking.accept(MAGDA, at=_hours(2))
    booking.accept(ANIA, at=_hours(3))

    booking.leave(MAGDA, at=CUT_OFF + timedelta(hours=2))

    [left] = booking.open_departures
    # Her own share paid her seat: a taker refunds her.
    assert (left.player_id, left.covered) == (MAGDA, False)
    assert not booking.short_at_the_cut_off(now=CUT_OFF + timedelta(hours=2))


# --------------------------------------------------------------------------- #
# Leaving
# --------------------------------------------------------------------------- #


def test_a_friend_who_accepted_leaves_before_the_cut_off_and_the_seat_is_empty():
    booking = _ania_said_no()

    booking.leave(EWA, at=WEDNESDAY)

    assert booking.state is BookingState.BOOKED
    assert EWA not in booking.players
    assert [(seat.seat_of, seat.how) for seat in booking.empty] == [
        (ANIA, Emptied.DECLINED),
        (EWA, Emptied.LEFT),
    ]
    assert not booking.rescuable_at(WEDNESDAY)
    assert _replayed(booking).empty == booking.empty


def test_a_whole_court_friend_leaving_after_the_cut_off_leaves_a_covered_seat():
    booking = _sent(PayMode.WHOLE_COURT)
    for friend, hour in ((EWA, 1), (MAGDA, 2), (ANIA, 3)):
        booking.accept(friend, at=_hours(hour))

    booking.leave(ANIA, at=CUT_OFF + timedelta(hours=1))

    [left] = booking.open_departures
    assert left.covered


def test_the_split_sender_leaving_before_the_cut_off_turns_the_game_ordinary():
    booking = _ania_said_no()
    booking.open_to_the_group(ANIA, at=_hours(4))

    booking.leave(TOMEK, at=WEDNESDAY)

    assert booking.ordinary and not booking.covering
    assert booking.sender_left_at == WEDNESDAY
    assert [(left.player_id, left.covered) for left in booking.open_departures] == [
        (ANIA, False),
        (TOMEK, False),
    ]
    assert booking.empty == ()
    # Short at the cut-off unless both seats are taken.
    assert booking.short_from == CUT_OFF
    assert booking.short_at_the_cut_off(now=CUT_OFF)
    # Nobody covers it now: no warning, and the cut-off opens nothing.
    assert not booking.cover_warning_due(CUT_OFF - timedelta(hours=1))
    assert booking.open_at_the_cut_off(at=CUT_OFF) == ()
    replayed = _replayed(booking)
    assert (replayed.ordinary, replayed.departures) == (True, booking.departures)


def test_an_ordinary_game_s_empty_seat_left_before_its_cut_off_calls_it_off():
    booking = _ania_said_no()
    booking.leave(TOMEK, at=WEDNESDAY)

    for player, hour in ((KUBA, 1), (MAREK, 2)):
        booking.rescue(player, at=WEDNESDAY + timedelta(hours=hour))

    assert booking.is_whole
    assert booking.short_from is None
    booking.leave(EWA, at=WEDNESDAY + timedelta(hours=3))
    # An ordinary leave now: a rescue at once, and short if nobody takes it.
    assert booking.rescuable_at(WEDNESDAY + timedelta(hours=3))
    assert booking.short_at_the_cut_off(now=CUT_OFF)


def test_an_unanswered_invitation_on_an_ordinary_game_makes_it_short():
    booking = _sent()
    booking.accept(EWA, at=_hours(1))
    booking.accept(MAGDA, at=_hours(2))
    booking.leave(TOMEK, at=_hours(3))
    booking.rescue(KUBA, at=_hours(4))

    # Ania's 24 hours end on Tuesday; her seat was never held since.
    assert booking.short_from == CUT_OFF
    booking.invited_seat_ran_out(ANIA, at=CUT_OFF + timedelta(minutes=1))
    [left] = booking.open_departures
    assert (left.player_id, left.at) == (ANIA, _hours(3))
    assert booking.short_at_the_cut_off(now=CUT_OFF)


def test_the_whole_court_sender_leaving_still_covers_his_own_seat():
    booking = _ania_said_no(PayMode.WHOLE_COURT)

    booking.leave(TOMEK, at=WEDNESDAY)

    assert booking.covering and not booking.ordinary
    [left] = booking.open_departures
    assert (left.player_id, left.covered) == (TOMEK, True)
    assert [seat.seat_of for seat in booking.empty] == [ANIA]
    assert booking.short_from is None
    # Its empty seat still opens at the cut-off.
    assert booking.open_at_the_cut_off(at=CUT_OFF) == (ANIA,)


def test_the_sender_leaving_after_the_cut_off_is_a_late_leaver():
    booking = _ania_said_no()
    booking.open_at_the_cut_off(at=CUT_OFF)

    booking.leave(TOMEK, at=CUT_OFF + timedelta(hours=1))

    assert booking.covering
    assert [(left.player_id, left.covered) for left in booking.open_departures] == [
        (ANIA, True),
        (TOMEK, False),
    ]
    assert not booking.short_at_the_cut_off(now=CUT_OFF + timedelta(hours=1))


def test_a_sender_who_left_calls_nothing_off():
    booking = _sent(PayMode.WHOLE_COURT)
    booking.leave(TOMEK, at=_hours(1))

    with pytest.raises(InvariantViolated):
        booking.call_off_by_the_sender(at=_hours(2))


# --------------------------------------------------------------------------- #
# The cover warning
# --------------------------------------------------------------------------- #


def test_the_split_sender_is_warned_once_a_day_before_the_cut_off():
    booking = _ania_said_no()
    warned_at = CUT_OFF - COVER_WARNING_BEFORE

    assert not booking.warn_the_cover(at=warned_at - timedelta(seconds=1))
    assert booking.warn_the_cover(at=warned_at)

    history = _recorded(booking)
    warned = history[-1]
    assert isinstance(warned, CoverWarned)
    assert (warned.sender_id, warned.seats) == (TOMEK, (ANIA,))
    assert not booking.warn_the_cover(at=warned_at + timedelta(hours=1))
    assert Booking.from_history(history).cover_warned_at == warned_at


def test_no_warning_with_every_seat_paid_by_its_own_player():
    booking = _sent()
    for friend, hour in ((EWA, 1), (MAGDA, 2), (ANIA, 3)):
        booking.accept(friend, at=_hours(hour))

    assert not booking.cover_warning_due(CUT_OFF - timedelta(hours=2))


def test_no_warning_with_whole_court_he_pays_every_seat_already():
    booking = _ania_said_no(PayMode.WHOLE_COURT)

    assert not booking.cover_warning_due(CUT_OFF - timedelta(hours=2))


def test_an_invitation_still_waiting_lacks_its_own_payment():
    booking = _sent()
    booking.accept(EWA, at=_hours(1))

    assert booking.unpaid_seats(now=_hours(2)) == (MAGDA, ANIA)


def test_an_opened_seat_nobody_took_lacks_its_own_payment_too():
    booking = _ania_said_no()
    booking.open_to_the_group(ANIA, at=WEDNESDAY)

    assert booking.unpaid_seats(now=WEDNESDAY) == (ANIA,)
    booking.rescue(MAREK, at=WEDNESDAY + timedelta(hours=1))
    assert booking.unpaid_seats(now=WEDNESDAY + timedelta(hours=1)) == ()


# --------------------------------------------------------------------------- #
# After review (#752)
# --------------------------------------------------------------------------- #


def test_a_whole_court_rescuer_who_leaves_late_paid_their_own_seat():
    """Kuba took the sender's seat and paid it himself: leaving after the
    cut-off, a taker refunds him — never a second cover of the sender's."""

    booking = _sent(PayMode.WHOLE_COURT)
    for friend, hour in ((EWA, 1), (MAGDA, 2), (ANIA, 3)):
        booking.accept(friend, at=_hours(hour))
    booking.leave(TOMEK, at=WEDNESDAY)
    booking.rescue(KUBA, at=WEDNESDAY + timedelta(hours=1))

    booking.leave(KUBA, at=CUT_OFF + timedelta(hours=1))

    [left] = booking.open_departures
    assert (left.player_id, left.covered) == (KUBA, False)


def test_the_split_sender_leaving_opens_a_seat_still_waiting_too():
    """§11.2: *his seat, and any seat no friend has taken, become rescues at
    once* — a friend still invited may still take theirs, first come."""

    booking = _sent()
    booking.accept(EWA, at=_hours(1))
    booking.decline(MAGDA, at=_hours(2))

    booking.leave(TOMEK, at=_hours(3))

    assert [left.player_id for left in booking.open_departures] == [
        TOMEK,
        MAGDA,
        ANIA,
    ]
    assert booking.waiting_at(_hours(4))[0].player_id == ANIA
    # Ania takes her own seat back: it is no longer open.
    booking.accept(ANIA, at=_hours(4))
    assert [left.player_id for left in booking.open_departures] == [TOMEK, MAGDA]
    assert ANIA in booking.players


def test_a_rescue_on_a_seat_still_waiting_ends_its_friends_invitation():
    booking = _sent()
    booking.accept(EWA, at=_hours(1))
    booking.accept(MAGDA, at=_hours(2))
    booking.leave(TOMEK, at=_hours(3))
    booking.rescue(KUBA, at=_hours(4))
    _recorded(booking)

    booking.rescue(MAREK, at=_hours(5))

    rescued, ended = _recorded(booking)
    assert isinstance(ended, InvitedSeatTaken)
    assert (ended.player_id, ended.taken_by) == (ANIA, MAREK)
    assert booking.is_whole
    # Ania's 24 hours ending later records nothing more.
    assert not booking.invited_seat_ran_out(ANIA, at=_hours(30))


def test_an_ordinary_game_s_unanswered_seat_is_open_since_the_sender_left():
    booking = _sent()
    booking.accept(EWA, at=_hours(1))
    booking.accept(MAGDA, at=_hours(2))
    booking.leave(TOMEK, at=_hours(3))
    booking.rescue(KUBA, at=_hours(4))

    [left] = booking.open_departures
    assert (left.player_id, left.at) == (ANIA, _hours(3))
    assert booking.short_at_the_cut_off(now=CUT_OFF)
    # Her time running out later opens nothing twice.
    booking.invited_seat_ran_out(ANIA, at=CUT_OFF + timedelta(minutes=1))
    assert len(booking.open_departures) == 1


def test_the_cover_line_reads_only_inside_the_day_before_the_cut_off():
    booking = _ania_said_no()

    assert booking.cover_line(now=CUT_OFF - COVER_WARNING_BEFORE) == (ANIA,)
    assert booking.cover_line(now=CUT_OFF - COVER_WARNING_BEFORE - timedelta(1)) == ()
    assert booking.cover_line(now=CUT_OFF) == ()
    assert _sent(PayMode.WHOLE_COURT).cover_line(now=CUT_OFF - timedelta(hours=1)) == ()
