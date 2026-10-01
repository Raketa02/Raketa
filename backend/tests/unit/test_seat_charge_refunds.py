"""A paid share given back (#544; the mechanics §12.3; ``docs/adr/0190`` §4).

**Raketa decides, the provider acts** — as with a capture: the refund is
decided in the act that causes it (a leaving before the cut-off, the minus the
card fee; a game called off at its cut-off, in full), and made at the provider
after the commit, which answers what it gave back and **the fee it withheld**.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.kernel import Sport, instant
from app.modules.payments.domain.events import (
    SeatChargeRefundDecided,
    SeatChargeRefunded,
)
from app.modules.payments.domain.provider import (
    Payment,
    PaymentStatus,
    Refund,
    RefundStatus,
)
from app.modules.payments.domain.seat_charge import SeatCharge, SeatChargeStatus

AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
GAME = instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc))
LATER = AT + timedelta(hours=1)


def a_paid_share() -> SeatCharge:
    charge = SeatCharge.held(
        charge_id=uuid4(),
        player_id=uuid4(),
        game_id=uuid4(),
        club_id=uuid4(),
        account_id="acct_1",
        payment=Payment(
            payment_id="pi_1", status=PaymentStatus.AUTHORISED, amount_grosze=30_00
        ),
        sport=Sport.PADEL,
        starts_at=GAME,
        at=AT,
    )
    charge.take(booking_id=charge.game_id, at=AT)
    charge.captured(at=AT)
    return charge


def test_a_paid_share_is_refunded_less_the_card_fee_and_records_the_fee_withheld():
    charge = a_paid_share()
    history = charge.pull_events()

    assert charge.refund(withhold_fee=True, at=LATER) is True
    assert charge.owes_a_refund
    assert charge.refunded(
        Refund(
            refund_id="re_1",
            status=RefundStatus.SUCCEEDED,
            amount_grosze=28_55,
            fee_withheld_grosze=1_45,
        ),
        at=LATER,
    )

    assert not charge.owes_a_refund
    assert charge.refund_given is not None
    assert (
        charge.refund_given.amount_grosze,
        charge.refund_given.fee_withheld_grosze,
    ) == (
        28_55,
        1_45,
    )
    decided, refunded = charge.pull_events()
    assert isinstance(decided, SeatChargeRefundDecided) and decided.withhold_fee
    assert isinstance(refunded, SeatChargeRefunded)
    replayed = SeatCharge.from_history([*history, decided, refunded])
    assert replayed.refund_given == charge.refund_given
    assert replayed.status is SeatChargeStatus.CAPTURED


def test_a_share_is_refunded_once():
    charge = a_paid_share()
    charge.refund(withhold_fee=False, at=LATER)
    charge.pull_events()

    assert charge.refund(withhold_fee=True, at=LATER) is False
    assert charge.refund_withholds_fee is False
    assert charge.pull_events() == []


def test_a_share_nobody_paid_is_never_refunded():
    charge = SeatCharge.held(
        charge_id=uuid4(),
        player_id=uuid4(),
        game_id=uuid4(),
        club_id=uuid4(),
        account_id="acct_1",
        payment=Payment(
            payment_id="pi_1", status=PaymentStatus.AUTHORISED, amount_grosze=30_00
        ),
        sport=Sport.PADEL,
        starts_at=GAME,
        at=AT,
    )
    charge.release(at=AT)

    assert charge.refund(withhold_fee=False, at=LATER) is False
