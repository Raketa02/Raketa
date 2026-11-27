"""A paid share given back (#544; the mechanics §12.3; ``docs/adr/0190`` §4).

**Rakieta decides, the provider acts** — as with a capture: the refund is
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


def a_paid_share(*, fee_grosze: int | None = 1_45) -> SeatCharge:
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
    charge.captured(at=AT, fee_grosze=fee_grosze)
    return charge


def test_a_paid_share_is_refunded_less_the_card_fee_and_records_the_fee_withheld():
    charge = a_paid_share()
    history = charge.pull_events()

    assert charge.refund(withhold_fee=True, at=LATER) is True
    assert charge.owes_a_refund
    assert charge.refund_to_ask_grosze == 28_55
    assert charge.refunded(
        Refund(refund_id="re_1", status=RefundStatus.SUCCEEDED, amount_grosze=28_55),
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


def test_a_refund_in_full_asks_for_the_whole_share():
    charge = a_paid_share()

    charge.refund(withhold_fee=False, at=LATER)

    assert charge.refund_to_ask_grosze == 30_00


def test_a_refund_less_the_fee_kept_is_exactly_the_fee_on_this_payment():
    """**Never an estimate** (ADR-0190's 2026-10-10 amendment): a business card
    kept 1,76 zł on a 40 zł share, so 38,24 zł goes back — and the record says
    the 1,76 zł was kept."""

    charge = a_paid_share(fee_grosze=1_76)
    charge.refund(withhold_fee=True, at=LATER)

    assert charge.refund_to_ask_grosze == 30_00 - 1_76
    charge.refunded(
        Refund(refund_id="re_1", status=RefundStatus.SUCCEEDED, amount_grosze=28_24),
        at=LATER,
    )
    assert charge.refund_given is not None
    assert charge.refund_given.fee_withheld_grosze == 1_76


def test_a_refund_less_a_fee_not_yet_known_waits_until_it_is():
    """A club on its own negotiated pricing is told its fee after the capture:
    until then there is no amount to ask for — and once it is reported, the
    refund is the share less exactly that."""

    charge = a_paid_share(fee_grosze=None)
    charge.refund(withhold_fee=True, at=LATER)

    assert charge.owes_a_refund
    assert charge.refund_to_ask_grosze is None

    assert charge.fee_reported(1_98, at=LATER) is True
    assert charge.refund_to_ask_grosze == 30_00 - 1_98
    assert SeatCharge.from_history(charge.pull_events()).fee_taken_grosze == 1_98


def test_a_fee_is_reported_once_and_only_on_a_share_taken():
    charge = a_paid_share()

    assert charge.fee_reported(1_98, at=LATER) is False  # it was known already
    assert charge.fee_taken_grosze == 1_45
