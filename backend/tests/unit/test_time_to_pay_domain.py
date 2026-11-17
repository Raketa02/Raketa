"""**Time to pay** on the Proposal (#625; the mechanics §12.2, Q109–Q111).

A share refused when a full game fills no longer reopens the seat at once:
**the reopening waits**. The player stays In, their seat held for them alone
until thirty minutes from the refusal, never past the book-by, and nobody else
may be dealt it or take it. Four ends, each a rule here:

- **paid in time** — the game books on the holds the others kept (the fill's,
  so here only what the stream says once it has);
- **paid, but a seat opened meanwhile** — they are In with their payment held,
  and the seat is no longer held for them (``TimeToPayMet``);
- **the time ran out** — their seat reopens, as Q24 always had it
  (``TimeToPayRanOut``);
- **somebody else left while it waited** — the game falls back to filling
  (``FellBackToFilling``), and the payer's time runs on.

**Which time it is** (#638; Q113): before the club's cut-off nothing is taken,
only held, so a refused share is **time to fix the card** — never past the
cut-off; from the cut-off on money is taken at once, and it is **time to pay**.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import InvariantViolated, Sport, instant
from app.modules.proposals.domain.errors import ProposalIsFull
from app.modules.proposals.domain.home import (
    BookingStage,
    CalledOffReason,
    without_a_booking,
)
from app.modules.proposals.domain.events import (
    FellBackToFilling,
    ProposalFilled,
    TimeToPayGiven,
    TimeToPayMet,
    TimeToPayRanOut,
    YesPaused,
    YesWithdrawn,
)
from app.modules.proposals.domain.limits import TIME_TO_PAY
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.proposal import (
    Origin,
    Proposal,
    ReopenReason,
    Reopened,
    Standing,
    TimeTo,
)

MADE_AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
START = instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc))
BOOK_BY = instant(datetime(2026, 10, 7, 15, tzinfo=timezone.utc))
FILLED_AT = instant(datetime(2026, 10, 6, 12, 10, tzinfo=timezone.utc))
PAY_BY = FILLED_AT + TIME_TO_PAY
#: Saturday's cut-off at a club that keeps the default 24 hours — after this
#: card's book-by, so every refusal here but the last section's is a card to fix.
CUT_OFF = START - timedelta(hours=24)

IVAN, MARTA, OSCAR, PAULA, DIEGO = (uuid4() for _ in range(5))
PAULAS_CHARGE = uuid4()


def a_card(*, book_by: datetime = BOOK_BY) -> Proposal:
    """Ivan, Marta, Oscar and Paula's card, dealt and not yet answered — its
    birth still to pull."""

    proposal = Proposal.make(
        proposal_id=uuid4(),
        pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
        origin=Origin.PICK,
        poster_id=None,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        club_id=uuid4(),
        start=START,
        share_grosze=40_00,
        book_by=instant(book_by),
        at=MADE_AT,
    )
    proposal.deal((MARTA, OSCAR, PAULA, IVAN), at=MADE_AT)
    for player in (MARTA, OSCAR, PAULA, IVAN):
        proposal.say_yes(player, at=MADE_AT)
    return proposal


def a_full_card(*, book_by: datetime = BOOK_BY) -> Proposal:
    """Ivan, Marta, Oscar and Paula, all In — the moment Ivan's yes filled
    it."""

    proposal = a_card(book_by=book_by)
    proposal.pull_events()
    return proposal


def paulas_bank_checks(
    proposal: Proposal,
    *,
    at: datetime = FILLED_AT,
    cut_off: datetime = CUT_OFF,
) -> Proposal:
    now = instant(at)
    proposal.give_time_to_pay(
        PAULA,
        reason=ReopenReason.AUTHENTICATION_REQUIRED,
        seat_charge_id=PAULAS_CHARGE,
        until=proposal.time_to_pay_ends(now, cut_off=instant(cut_off)) or now,
        time_to=TimeTo.at(now, cut_off=instant(cut_off)),
        filled_by=IVAN,
        at=now,
    )
    return proposal


# --------------------------------------------------------------------------- #
# The seat is held for her alone
# --------------------------------------------------------------------------- #


def test_a_refused_share_keeps_its_player_in_with_the_seat_held_for_her():
    proposal = paulas_bank_checks(a_full_card())

    [given] = proposal.pull_events()

    assert isinstance(given, TimeToPayGiven)
    assert (given.player_id, given.seat_charge_id, given.reason) == (
        PAULA,
        PAULAS_CHARGE,
        "AUTHENTICATION_REQUIRED",
    )
    assert given.until == PAY_BY
    assert given.filled_by == IVAN
    assert PAULA in proposal.yeses
    assert proposal.open_seats == 0
    assert proposal.waiting_for_a_payment is True
    assert proposal.paying[PAULA].until == PAY_BY
    assert proposal.paying[PAULA].payment_to_confirm == PAULAS_CHARGE
    assert proposal.standing_at(PAY_BY) is Standing.FILLING


def test_nobody_else_may_take_a_seat_held_for_its_payer():
    """Diego was dealt the card too: while Paula's time runs, the game is full
    to him."""

    proposal = Proposal.make(
        proposal_id=uuid4(),
        pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
        origin=Origin.PICK,
        poster_id=None,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        club_id=uuid4(),
        start=START,
        share_grosze=40_00,
        book_by=BOOK_BY,
        at=MADE_AT,
    )
    proposal.deal((MARTA, OSCAR, PAULA), at=MADE_AT)
    proposal.deal((DIEGO,), at=MADE_AT)
    for player in (MARTA, OSCAR, PAULA):
        proposal.say_yes(player, at=MADE_AT)
    proposal.say_yes(DIEGO, at=MADE_AT)
    proposal.withdraw_yes(DIEGO, at=MADE_AT)
    proposal.deal((IVAN,), at=MADE_AT, into=2)
    proposal.say_yes(IVAN, at=MADE_AT)
    paulas_bank_checks(proposal)

    with pytest.raises(ProposalIsFull):
        proposal.say_yes(DIEGO, at=FILLED_AT)


def test_the_time_to_pay_is_thirty_minutes_never_past_the_book_by():
    assert a_full_card().time_to_pay_ends(
        FILLED_AT, cut_off=CUT_OFF
    ) == FILLED_AT + timedelta(minutes=30)
    close = BOOK_BY - timedelta(minutes=10)
    assert a_full_card().time_to_pay_ends(close, cut_off=CUT_OFF) == BOOK_BY
    # No time is left from the book-by on.
    assert a_full_card().time_to_pay_ends(BOOK_BY, cut_off=CUT_OFF) is None


def test_a_payer_refused_again_keeps_her_time_and_it_never_moves():
    proposal = paulas_bank_checks(a_full_card())
    later = FILLED_AT + timedelta(minutes=12)

    proposal.give_time_to_pay(
        PAULA,
        reason=ReopenReason.TERMS_NEEDED,
        seat_charge_id=uuid4(),
        until=proposal.time_to_pay_ends(later, cut_off=CUT_OFF) or later,
        time_to=TimeTo.at(later, cut_off=CUT_OFF),
        filled_by=PAULA,
        at=later,
    )

    assert proposal.paying[PAULA].until == PAY_BY
    assert proposal.paying[PAULA].reason is ReopenReason.TERMS_NEEDED
    assert proposal.paying[PAULA].payment_to_confirm is None
    # Her payment to confirm arrived with the first refusal (#815).
    assert proposal.paying[PAULA].refused_at == FILLED_AT


def test_a_refused_share_arrives_when_it_was_refused():
    """What *Needs your answer* dates her payment to confirm by (#815)."""

    proposal = paulas_bank_checks(a_full_card())

    assert proposal.paying[PAULA].refused_at == FILLED_AT


def test_a_payment_to_confirm_arrives_when_it_came_to_need_confirming():
    """Refused first for her terms — nothing to confirm, only terms to accept
    again — then by her bank within her time: the payment to confirm arrived
    with the second refusal, never the first (#815)."""

    proposal = a_full_card()
    proposal.give_time_to_pay(
        PAULA,
        reason=ReopenReason.TERMS_NEEDED,
        seat_charge_id=uuid4(),
        until=PAY_BY,
        time_to=TimeTo.at(FILLED_AT, cut_off=CUT_OFF),
        filled_by=IVAN,
        at=FILLED_AT,
    )
    assert proposal.paying[PAULA].payment_to_confirm is None
    later = FILLED_AT + timedelta(minutes=12)

    proposal.give_time_to_pay(
        PAULA,
        reason=ReopenReason.DECLINED,
        seat_charge_id=PAULAS_CHARGE,
        until=PAY_BY,
        time_to=TimeTo.at(later, cut_off=CUT_OFF),
        filled_by=PAULA,
        at=later,
    )

    assert proposal.paying[PAULA].payment_to_confirm == PAULAS_CHARGE
    assert proposal.paying[PAULA].refused_at == later


def test_a_seat_reopened_with_no_time_to_pay_arrives_when_it_reopened():
    proposal = a_full_card()
    refused = FILLED_AT + timedelta(minutes=3)

    proposal.reopen_seat(
        PAULA,
        reason=ReopenReason.DECLINED,
        seat_charge_id=PAULAS_CHARGE,
        at=refused,
    )

    assert proposal.reopened[PAULA].refused_at == refused


def test_time_to_pay_is_given_only_to_somebody_in_on_a_full_game():
    proposal = a_full_card()
    proposal.withdraw_yes(OSCAR, at=FILLED_AT)

    with pytest.raises(InvariantViolated):
        paulas_bank_checks(proposal)


# --------------------------------------------------------------------------- #
# The four ends
# --------------------------------------------------------------------------- #


def test_the_time_running_out_reopens_her_seat_as_a_refused_payment_does():
    proposal = paulas_bank_checks(a_full_card())
    proposal.pull_events()

    assert proposal.run_out_of_time(at=PAY_BY - timedelta(seconds=1)) == ()
    lapsed = proposal.run_out_of_time(at=PAY_BY)

    assert lapsed == (PAULA,)
    [ran_out] = proposal.pull_events()
    assert isinstance(ran_out, TimeToPayRanOut)
    assert ran_out.player_ids == (PAULA,)
    assert PAULA not in proposal.yeses
    # Fix your card becomes Confirm: still the payment refused at the fill,
    # so it arrived then, not now (#815).
    assert proposal.reopened[PAULA] == Reopened(
        reason=ReopenReason.AUTHENTICATION_REQUIRED,
        seat_charge_id=PAULAS_CHARGE,
        refused_at=FILLED_AT,
    )
    assert proposal.paying == {}
    assert proposal.open_seats == 1
    assert proposal.waiting_for_a_payment is False
    # It fell back: nobody else's payment is awaited, and it is filling.
    assert proposal.fell_back_at == PAY_BY
    assert proposal.ran_out_for_good is False
    assert proposal.run_out_of_time(at=PAY_BY) == ()


def test_a_time_to_pay_cut_short_at_the_book_by_runs_out_for_good():
    proposal = paulas_bank_checks(a_full_card(), at=BOOK_BY - timedelta(minutes=5))

    assert proposal.paying[PAULA].until == BOOK_BY
    # Past the book-by the game is over, and her time still runs out on it.
    assert proposal.run_out_of_time(at=BOOK_BY + timedelta(seconds=20)) == (PAULA,)
    assert proposal.ran_out_for_good is True


def test_paying_in_time_with_a_seat_open_keeps_her_in_with_nothing_held():
    proposal = paulas_bank_checks(a_full_card())
    proposal.withdraw_yes(OSCAR, at=FILLED_AT + timedelta(minutes=5))
    proposal.pull_events()

    proposal.time_to_pay_met(PAULA, at=FILLED_AT + timedelta(minutes=9))

    [met] = proposal.pull_events()
    assert isinstance(met, TimeToPayMet)
    assert PAULA in proposal.yeses
    assert proposal.paying == {}
    assert proposal.run_out_of_time(at=PAY_BY) == ()


def test_the_game_filled_on_her_payment_says_so():
    proposal = paulas_bank_checks(a_full_card())

    proposal.fill(
        first_side=(MARTA, OSCAR),
        second_side=(PAULA, IVAN),
        by=PAULA,
        at=FILLED_AT + timedelta(minutes=9),
    )

    assert proposal.paying == {}
    assert proposal.booked_on_a_payment is True
    assert proposal.filled_by == PAULA
    assert a_full_card().booked_on_a_payment is False


# --------------------------------------------------------------------------- #
# Somebody else's seat opening while it waits
# --------------------------------------------------------------------------- #


def test_a_leave_while_it_waits_falls_the_game_back_naming_the_leaver():
    proposal = paulas_bank_checks(a_full_card())
    proposal.pull_events()
    at = FILLED_AT + timedelta(minutes=4)

    proposal.withdraw_yes(OSCAR, at=at)

    withdrawn, fell_back = proposal.pull_events()
    assert isinstance(withdrawn, YesWithdrawn)
    assert isinstance(fell_back, FellBackToFilling)
    assert (fell_back.player_ids, fell_back.left) == ((OSCAR,), (OSCAR,))
    # Her time runs on.
    assert proposal.paying[PAULA].until == PAY_BY
    assert proposal.waiting_for_a_payment is False
    assert proposal.fell_back_at == at


def test_a_week_that_filled_while_it_waits_falls_it_back_naming_nobody():
    proposal = paulas_bank_checks(a_full_card())
    proposal.pull_events()

    assert proposal.pause_yes(MARTA, at=FILLED_AT + timedelta(minutes=4))

    paused, fell_back = proposal.pull_events()
    assert isinstance(paused, YesPaused)
    assert isinstance(fell_back, FellBackToFilling)
    assert (fell_back.player_ids, fell_back.left) == ((MARTA,), ())


def test_the_payer_leaving_gives_up_her_seat_and_her_time():
    proposal = paulas_bank_checks(a_full_card())
    proposal.pull_events()

    proposal.withdraw_yes(PAULA, at=FILLED_AT + timedelta(minutes=4))

    _, fell_back = proposal.pull_events()
    assert isinstance(fell_back, FellBackToFilling)
    assert fell_back.left == (PAULA,)
    assert proposal.paying == {}
    assert PAULA not in proposal.reopened


def test_a_game_waiting_for_a_payment_is_on_home():
    proposal = paulas_bank_checks(a_full_card())

    assert proposal.payment_awaited_at == FILLED_AT
    assert a_full_card().payment_awaited_at is None


def test_the_stream_folds_back_to_the_same_wait():
    proposal = paulas_bank_checks(a_card())
    proposal.withdraw_yes(OSCAR, at=FILLED_AT + timedelta(minutes=4))

    replayed = Proposal.from_history(proposal.pull_events())

    assert replayed.paying == proposal.paying
    assert replayed.fell_back_at == proposal.fell_back_at
    assert replayed.payment_awaited_at == FILLED_AT
    assert replayed.version == proposal.version


def test_a_filled_game_was_never_waiting_for_a_payment():
    proposal = a_full_card()
    proposal.fill(
        first_side=(MARTA, OSCAR), second_side=(PAULA, IVAN), by=IVAN, at=FILLED_AT
    )

    events = proposal.pull_events()

    assert [type(event) for event in events] == [ProposalFilled]
    assert proposal.waiting_for_a_payment is False


# --------------------------------------------------------------------------- #
# Home's card for a game with no booking (#625)
# --------------------------------------------------------------------------- #


def test_a_game_waiting_for_a_payment_is_read_off_its_proposal():
    proposal = paulas_bank_checks(a_full_card())

    waiting = without_a_booking(proposal, now=FILLED_AT)

    assert waiting.stage is BookingStage.WAITING_FOR_A_PAYMENT
    assert waiting.booking_id == proposal.proposal_id
    assert waiting.paying == {PAULA: PAY_BY}
    assert (waiting.game_id, waiting.court_given) == (None, False)
    assert set(waiting.players) == {MARTA, OSCAR, PAULA, IVAN}

    proposal.run_out_of_time(at=PAY_BY)
    fell_back = without_a_booking(proposal, now=PAY_BY)
    assert (fell_back.stage, fell_back.called_off) == (BookingStage.FILLING_AGAIN, None)
    assert PAULA not in fell_back.players
    assert fell_back.open_seats == 1

    over = without_a_booking(proposal, now=BOOK_BY)
    assert over.called_off is CalledOffReason.BOOK_BY_PASSED


def test_a_game_whose_time_ran_out_at_its_book_by_was_a_payment_not_in_time():
    proposal = paulas_bank_checks(a_full_card(), at=BOOK_BY - timedelta(minutes=5))

    # The job has not run: the clock already says the payment did not come.
    assert (
        without_a_booking(proposal, now=BOOK_BY).called_off
        is CalledOffReason.PAYMENT_NOT_IN_TIME
    )
    proposal.run_out_of_time(at=BOOK_BY)
    assert (
        without_a_booking(proposal, now=BOOK_BY).called_off
        is CalledOffReason.PAYMENT_NOT_IN_TIME
    )


def test_a_yes_another_booking_withdrew_while_it_waits_falls_it_back_unnamed():
    """Oscar's hour went to another game of his: not his own act, so nobody is
    told his name (Q104)."""

    proposal = paulas_bank_checks(a_full_card())
    proposal.pull_events()

    proposal.withdraw_yes(OSCAR, at=FILLED_AT + timedelta(minutes=4), own=False)

    _, fell_back = proposal.pull_events()
    assert isinstance(fell_back, FellBackToFilling)
    assert (fell_back.player_ids, fell_back.left) == ((OSCAR,), ())


def test_her_payment_in_time_stays_hers_until_the_game_fills():
    proposal = paulas_bank_checks(a_full_card())
    proposal.withdraw_yes(OSCAR, at=FILLED_AT + timedelta(minutes=4))

    proposal.time_to_pay_met(PAULA, at=FILLED_AT + timedelta(minutes=9))

    assert proposal.paid_in_time == {PAULA: PAULAS_CHARGE}
    proposal.withdraw_yes(PAULA, at=FILLED_AT + timedelta(minutes=10))
    assert proposal.paid_in_time == {}


# --------------------------------------------------------------------------- #
# Time to fix the card, or time to pay (#638; Q113)
# --------------------------------------------------------------------------- #

#: A card whose book-by is two hours before its hour — after its cut-off, as a
#: club's usually is.
LATE_BOOK_BY = START - timedelta(hours=2)


def test_before_the_cut_off_a_refused_share_is_time_to_fix_the_card():
    proposal = paulas_bank_checks(a_full_card())

    [given] = proposal.pull_events()

    assert isinstance(given, TimeToPayGiven)
    assert given.time_to == "FIX_THE_CARD"
    assert proposal.paying[PAULA].time_to is TimeTo.FIX_THE_CARD
    assert proposal.time_to is TimeTo.FIX_THE_CARD


def test_from_the_cut_off_on_it_is_time_to_pay():
    assert TimeTo.at(CUT_OFF - timedelta(seconds=1), cut_off=CUT_OFF) is (
        TimeTo.FIX_THE_CARD
    )
    assert TimeTo.at(CUT_OFF, cut_off=CUT_OFF) is TimeTo.PAY

    proposal = paulas_bank_checks(
        a_full_card(book_by=LATE_BOOK_BY), at=CUT_OFF + timedelta(hours=1)
    )

    [given] = proposal.pull_events()
    assert given.time_to == "PAY"
    assert proposal.time_to is TimeTo.PAY
    assert proposal.paying[PAULA].until == CUT_OFF + timedelta(hours=1, minutes=30)


def test_time_to_fix_the_card_never_runs_past_the_cut_off():
    card = a_full_card(book_by=LATE_BOOK_BY)
    close = CUT_OFF - timedelta(minutes=10)

    assert card.time_to_pay_ends(close, cut_off=CUT_OFF) == CUT_OFF
    # From the cut-off on it is time to pay: thirty minutes, to the book-by.
    assert card.time_to_pay_ends(CUT_OFF, cut_off=CUT_OFF) == CUT_OFF + TIME_TO_PAY


def test_nobody_s_time_is_anything_while_no_payment_is_awaited():
    assert a_full_card().time_to is None


def test_a_payer_refused_again_keeps_what_her_time_is_for():
    proposal = paulas_bank_checks(a_full_card())
    later = FILLED_AT + timedelta(minutes=12)

    proposal.give_time_to_pay(
        PAULA,
        reason=ReopenReason.TERMS_NEEDED,
        seat_charge_id=uuid4(),
        until=later + TIME_TO_PAY,
        time_to=TimeTo.PAY,
        filled_by=PAULA,
        at=later,
    )

    assert proposal.paying[PAULA].time_to is TimeTo.FIX_THE_CARD


def test_running_out_says_whose_time_was_to_fix_the_card():
    fixing = paulas_bank_checks(a_full_card())
    fixing.pull_events()
    paying = paulas_bank_checks(
        a_full_card(book_by=LATE_BOOK_BY), at=CUT_OFF + timedelta(hours=1)
    )
    paying.pull_events()

    fixing.run_out_of_time(at=PAY_BY)
    paying.run_out_of_time(at=CUT_OFF + timedelta(hours=2))

    [fixed_out] = fixing.pull_events()
    [paid_out] = paying.pull_events()
    assert isinstance(fixed_out, TimeToPayRanOut)
    assert isinstance(paid_out, TimeToPayRanOut)
    assert (fixed_out.player_ids, fixed_out.fixing) == ((PAULA,), (PAULA,))
    assert (paid_out.player_ids, paid_out.fixing) == ((PAULA,), ())


def test_a_time_to_pay_recorded_before_there_were_two_is_time_to_pay():
    """A stream written before #638 says nothing of what its time was for: it
    was time to pay, the only one there was."""

    proposal = a_card()
    events = proposal.pull_events()
    given = TimeToPayGiven(
        proposal_id=proposal.proposal_id,
        player_id=PAULA,
        seat_charge_id=PAULAS_CHARGE,
        reason="AUTHENTICATION_REQUIRED",
        until=PAY_BY,
        occurred_at=FILLED_AT,
    )

    replayed = Proposal.from_history([*events, given])

    assert replayed.paying[PAULA].time_to is TimeTo.PAY
    ran_out = TimeToPayRanOut(
        proposal_id=proposal.proposal_id, player_ids=(PAULA,), occurred_at=PAY_BY
    )
    assert ran_out.fixing == ()


def test_a_game_with_no_booking_reads_what_its_time_is_for():
    proposal = paulas_bank_checks(a_full_card())

    assert without_a_booking(proposal, now=FILLED_AT).time_to is TimeTo.FIX_THE_CARD
    proposal.run_out_of_time(at=PAY_BY)
    assert without_a_booking(proposal, now=PAY_BY).time_to is None
