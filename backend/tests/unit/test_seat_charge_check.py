"""**A game that fills far ahead is checked, and held at its Holding time**
(#639; the mechanics Q113; ADR-0189's 2026-10-10 amendment).

A card hold made without its player lasts days, not until the game: 4 days 18
hours on a Visa, 7 days on a Mastercard. A hold **reaches** the club's cut-off
when its last moment is at least six hours after it; one that does not is let
go at once — a **Card check** — and the share is held again at its **Holding
time**, four days before the cut-off. A holding that still falls short is taken
at its last safe moment.

The Seat charge's moves: checked → held again → taken; checked → closed by a
leave; checked → refused at its holding → confirmed → held.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.kernel import Sport, instant
from app.modules.payments.domain.provider import Payment, PaymentStatus
from app.modules.payments.domain.seat_charge import (
    PAID,
    FailureReason,
    RefundReason,
    SeatCharge,
    SeatChargeStatus,
    holding_time,
    reaches,
    taken_by,
)

#: Thursday 1 October 2026, 19:00 in Kraków: the game fills a week ahead.
FILLED = instant(datetime(2026, 10, 1, 17, tzinfo=timezone.utc))
#: Its cut-off: Wednesday 7 October, 19:00.
CUT_OFF = instant(datetime(2026, 10, 7, 17, tzinfo=timezone.utc))
#: Thursday 8 October, 19:00.
GAME = instant(datetime(2026, 10, 8, 17, tzinfo=timezone.utc))
#: Saturday 3 October, 19:00: four days before the cut-off.
HOLDING = instant(datetime(2026, 10, 3, 17, tzinfo=timezone.utc))


def a_payment(
    status: PaymentStatus = PaymentStatus.AUTHORISED,
    *,
    payment_id: str = "pi_check",
    lasts: timedelta | None = timedelta(days=4, hours=18),
    at=FILLED,
) -> Payment:
    return Payment(
        payment_id=payment_id,
        status=status,
        amount_grosze=40_00,
        last_moment=(
            instant(at + lasts)
            if lasts is not None and status is PaymentStatus.AUTHORISED
            else None
        ),
    )


def a_check() -> SeatCharge:
    """Ivan's Visa, held at the fill and checked: it would not last until
    Wednesday."""

    charge = SeatCharge.held(
        charge_id=uuid4(),
        player_id=uuid4(),
        game_id=uuid4(),
        club_id=uuid4(),
        account_id="acct_1",
        payment=a_payment(),
        sport=Sport.PADEL,
        starts_at=GAME,
        at=FILLED,
    )
    charge.check(booking_id=charge.game_id, until=CUT_OFF, hold_at=HOLDING, at=FILLED)
    return charge


# --------------------------------------------------------------------------- #
# The reach rule
# --------------------------------------------------------------------------- #


def test_a_hold_reaches_the_cut_off_with_six_hours_to_spare():
    assert reaches(instant(CUT_OFF + timedelta(hours=6)), cut_off=CUT_OFF)
    assert not reaches(
        instant(CUT_OFF + timedelta(hours=5, minutes=59)), cut_off=CUT_OFF
    )


def test_a_hold_whose_last_moment_the_provider_did_not_say_reaches():
    assert reaches(None, cut_off=CUT_OFF)


def test_a_visa_held_a_week_ahead_does_not_reach_and_a_mastercard_does():
    visa = instant(FILLED + timedelta(days=4, hours=18))
    mastercard = instant(FILLED + timedelta(days=7))

    assert not reaches(visa, cut_off=CUT_OFF)
    assert reaches(mastercard, cut_off=CUT_OFF)


def test_the_holding_time_is_four_days_before_the_cut_off():
    assert holding_time(CUT_OFF) == HOLDING


def test_a_holding_that_reaches_is_taken_at_the_cut_off():
    lasts = instant(HOLDING + timedelta(days=4, hours=18))

    assert taken_by(lasts, cut_off=CUT_OFF) == CUT_OFF


def test_a_holding_that_falls_short_is_taken_at_its_last_safe_moment():
    lasts = instant(HOLDING + timedelta(days=2))

    assert taken_by(lasts, cut_off=CUT_OFF) == instant(lasts - timedelta(hours=6))


# --------------------------------------------------------------------------- #
# Checked → held → taken
# --------------------------------------------------------------------------- #


def test_a_checked_share_is_neither_held_nor_paid_nor_settled():
    charge = a_check()

    assert charge.status is SeatChargeStatus.CHECKED
    assert charge.status not in PAID
    assert charge.hold_at == HOLDING
    assert charge.held_until == CUT_OFF
    assert charge.booking_id == charge.game_id
    assert not charge.settled
    assert not charge.held_now


def test_the_holding_holds_a_checked_share_again_on_a_new_payment():
    charge = a_check()
    charge.pull_events()
    holding = a_payment(payment_id="pi_holding", at=HOLDING)

    charge.hold_again(holding, until=CUT_OFF, at=HOLDING)

    assert charge.status is SeatChargeStatus.HELD
    assert charge.payment_id == "pi_holding"
    assert charge.last_moment == holding.last_moment
    assert charge.held_until == CUT_OFF
    assert charge.take_at_the_cut_off(at=CUT_OFF)
    assert charge.status is SeatChargeStatus.TAKING


def test_a_checked_share_closed_by_a_leave_lets_nothing_go_and_is_no_receipt():
    charge = a_check()

    assert charge.let_go(at=HOLDING, reason=RefundReason.LEFT)

    assert charge.status is SeatChargeStatus.CANCELLED
    # Never a receipt: nothing was held for the game when it was given up.
    assert charge.released_at is None
    assert charge.settled


def test_the_check_s_payment_cancelled_at_the_provider_moves_nothing():
    charge = a_check()
    charge.pull_events()

    assert charge.heard(a_payment(PaymentStatus.CANCELLED), at=FILLED) is False
    assert charge.status is SeatChargeStatus.CHECKED
    assert charge.pull_events() == []


def test_an_undecided_release_never_touches_a_checked_share():
    charge = a_check()

    assert charge.release(at=HOLDING) is False
    assert charge.status is SeatChargeStatus.CHECKED


# --------------------------------------------------------------------------- #
# A refused holding: time to fix the card
# --------------------------------------------------------------------------- #


def test_a_refused_holding_waits_for_its_player_on_the_new_payment():
    charge = a_check()

    charge.holding_refused(
        FailureReason.DECLINED,
        payment=a_payment(PaymentStatus.DECLINED, payment_id="pi_holding"),
        at=HOLDING,
    )

    assert charge.status is SeatChargeStatus.FAILED
    assert charge.failure is FailureReason.DECLINED
    assert charge.payment_id == "pi_holding"
    assert charge.awaits_its_player
    assert charge.refused_at_its_holding
    assert charge.booking_id == charge.game_id


def test_a_refused_holding_fixed_in_time_is_held_until_the_cut_off():
    charge = a_check()
    charge.holding_refused(
        FailureReason.AUTHENTICATION_REQUIRED,
        payment=a_payment(
            PaymentStatus.AUTHENTICATION_REQUIRED, payment_id="pi_holding"
        ),
        at=HOLDING,
    )
    confirmed = instant(HOLDING + timedelta(minutes=10))
    charge.confirm(at=confirmed, last_moment=instant(confirmed + timedelta(days=7)))

    charge.keep(booking_id=charge.game_id, until=CUT_OFF, at=confirmed, fixed=True)

    assert charge.status is SeatChargeStatus.HELD
    assert not charge.refused_at_its_holding
    assert charge.pull_events()[-1].fixed is True


def test_a_refused_holding_with_no_payment_is_held_on_the_first_one():
    charge = a_check()
    charge.holding_refused(FailureReason.TERMS_NEEDED, payment=None, at=HOLDING)
    assert charge.payment_id is None
    assert not charge.awaits_its_player

    fixed = instant(HOLDING + timedelta(minutes=5))
    charge.hold_again(
        a_payment(payment_id="pi_after_the_terms", at=fixed), until=CUT_OFF, at=fixed
    )

    assert charge.status is SeatChargeStatus.HELD
    assert charge.payment_id == "pi_after_the_terms"


def test_a_refused_holding_is_the_booked_game_s_to_let_go_never_an_undecided_one():
    charge = a_check()
    charge.holding_refused(
        FailureReason.DECLINED,
        payment=a_payment(PaymentStatus.DECLINED, payment_id="pi_holding"),
        at=HOLDING,
    )

    assert charge.release(at=HOLDING) is False
    assert charge.let_go(at=HOLDING) is True
    assert charge.status is SeatChargeStatus.RELEASING
    assert charge.released_at is None
