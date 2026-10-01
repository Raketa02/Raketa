"""A Seat charge hears the provider **only forward** (#541; ``docs/adr/0190``
§3): notices arrive twice and out of order, so a reading the charge has
already moved past is the past arriving late and records nothing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.kernel import Sport, instant
from app.modules.payments.domain.provider import Payment, PaymentStatus
from app.modules.payments.domain.seat_charge import (
    FailureReason,
    SeatCharge,
    SeatChargeStatus,
)

AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
GAME = instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc))


def payment(status: PaymentStatus) -> Payment:
    return Payment(payment_id="pi_1", status=status, amount_grosze=30_00)


def a_hold() -> SeatCharge:
    return SeatCharge.held(
        charge_id=uuid4(),
        player_id=uuid4(),
        game_id=uuid4(),
        club_id=uuid4(),
        account_id="acct_1",
        payment=payment(PaymentStatus.AUTHORISED),
        sport=Sport.PADEL,
        starts_at=GAME,
        at=AT,
    )


def a_refusal() -> SeatCharge:
    return SeatCharge.refused(
        charge_id=uuid4(),
        player_id=uuid4(),
        game_id=uuid4(),
        club_id=uuid4(),
        account_id="acct_1",
        amount_grosze=30_00,
        sport=Sport.PADEL,
        starts_at=GAME,
        reason=FailureReason.AUTHENTICATION_REQUIRED,
        payment=payment(PaymentStatus.AUTHENTICATION_REQUIRED),
        at=AT,
    )


def test_a_hold_heard_after_its_capture_records_nothing():
    charge = a_hold()
    charge.take(booking_id=uuid4(), at=AT)
    charge.heard(payment(PaymentStatus.CAPTURED), at=AT)
    charge.pull_events()

    assert charge.heard(payment(PaymentStatus.AUTHORISED), at=AT) is False
    assert charge.status is SeatChargeStatus.CAPTURED
    assert charge.pull_events() == []


def test_a_capture_heard_twice_is_recorded_once():
    charge = a_hold()
    charge.take(booking_id=uuid4(), at=AT)

    assert charge.heard(payment(PaymentStatus.CAPTURED), at=AT) is True
    assert charge.heard(payment(PaymentStatus.CAPTURED), at=AT) is False


def test_a_refused_payment_its_player_confirmed_is_held_again():
    charge = a_refusal()

    assert charge.heard(payment(PaymentStatus.AUTHORISED), at=AT) is True
    assert charge.held_now


def test_a_hold_the_provider_let_go_on_its_own_is_no_longer_held():
    """A hold the provider dropped — never decided here — must not be taken by
    the next fill: it is cancelled, and the next fill asks afresh."""

    charge = a_hold()

    assert charge.heard(payment(PaymentStatus.CANCELLED), at=AT) is True
    assert charge.status is SeatChargeStatus.CANCELLED
    assert not charge.held_now


def test_a_taken_charge_is_never_heard_cancelled():
    charge = a_hold()
    charge.take(booking_id=uuid4(), at=AT)

    assert charge.heard(payment(PaymentStatus.CANCELLED), at=AT) is False
    assert charge.status is SeatChargeStatus.TAKING
