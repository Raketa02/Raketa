"""The fake provider models what holding a share until the cut-off tests
(ADR-0190's 2026-10-10 amendment; the mechanics Q113, Appendix A).

**Card kinds, each with its real fee.** What Stripe keeps on a payment depends
on the card: a personal card issued in the EU, a business card, a UK card, a
card from outside Europe. The fake keeps exactly that kind's fee when the
money is taken, and never an estimate — so a late leaver's refund, the share
less the fee kept on *their* payment, comes out to the grosz.

**Hold windows, on its clock.** A hold made without the player present lasts 4
days 18 hours on a Visa and 7 days on a Mastercard; one the player confirmed in
the app lasts 7 days on either. A capture after the last moment is refused, and
the payment ends cancelled — the hold lapsed, as at Stripe.

**A fee not yet known.** A club on its own negotiated pricing is told the fee
later than the capture, and the fake says *not yet known* until it is.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.kernel import instant
from app.modules.payments.domain.entered_cards import (
    A_CARD,
    A_CARD_THAT_DECLINES_LATER,
    CardKind,
    EnteredCard,
)
from app.modules.payments.domain.provider import PaymentStatus
from app.modules.payments.infrastructure.fake_payments import FakePayments, FakeRefusal
from app.shared.ids import new_uuid
from tests.unit.fake_clock import MovableClock

ACCOUNT = "acct_fake_club"
MONDAY = instant(datetime(2026, 10, 12, 9, tzinfo=timezone.utc))


def _a_fake() -> tuple[FakePayments, MovableClock]:
    clock = MovableClock(MONDAY)
    return FakePayments(clock=clock), clock


async def _a_hold(
    fake: FakePayments, card: EnteredCard = A_CARD, *, amount_grosze: int = 40_00
) -> str:
    customer = await fake.open_customer(player_id=new_uuid(), idempotency_key="c")
    setup = await fake.start_setup(
        customer_id=customer, player_id=new_uuid(), idempotency_key="s"
    )
    fake.phone_enters(setup.setup_id, card)
    saved = (await fake.read_setup(setup.setup_id)).card
    assert saved is not None
    clone = await fake.clone_method(
        customer_id=customer,
        method_id=saved.method_id,
        account_id=ACCOUNT,
        idempotency_key="k",
    )
    held = await fake.authorise(
        account_id=ACCOUNT,
        method_id=clone,
        amount_grosze=amount_grosze,
        description="Padel",
        metadata={},
        idempotency_key="h",
    )
    return held.payment_id


# --------------------------------------------------------------------------- #
# Card kinds
# --------------------------------------------------------------------------- #


def test_the_card_every_test_types_is_a_personal_card_issued_in_the_eu():
    assert A_CARD.kind is CardKind.PERSONAL_EU


@pytest.mark.parametrize(
    ("kind", "fee"),
    [
        (CardKind.PERSONAL_EU, 1_60),  # 1,5 % + 1 zł
        (CardKind.BUSINESS, 1_76),  # 1,9 % + 1 zł
        (CardKind.UK, 2_00),  # 2,5 % + 1 zł
        (CardKind.OUTSIDE_EUROPE, 2_30),  # 3,25 % + 1 zł
    ],
)
async def test_a_share_taken_keeps_its_card_kind_s_real_fee(kind, fee):
    fake, _ = _a_fake()
    payment = await _a_hold(fake, replace(A_CARD, kind=kind))

    taken = await fake.capture(
        account_id=ACCOUNT, payment_id=payment, idempotency_key="t"
    )
    read = await fake.read_payment(account_id=ACCOUNT, payment_id=payment)

    assert taken.fee_grosze == fee
    assert read.fee_grosze == fee


async def test_a_fee_is_rounded_to_the_nearest_grosz_half_up():
    fake, _ = _a_fake()
    payment = await _a_hold(fake, amount_grosze=30_00)

    taken = await fake.capture(
        account_id=ACCOUNT, payment_id=payment, idempotency_key="t"
    )

    assert taken.fee_grosze == 1_45  # 1,5 % of 30 zł is 45 grosze, and 1 zł


async def test_a_saved_card_s_kind_can_be_set_for_its_next_payment():
    fake, _ = _a_fake()
    customer = await fake.open_customer(player_id=new_uuid(), idempotency_key="c")
    setup = await fake.start_setup(
        customer_id=customer, player_id=new_uuid(), idempotency_key="s"
    )
    fake.phone_enters(setup.setup_id, A_CARD)
    saved = (await fake.read_setup(setup.setup_id)).card
    assert saved is not None

    fake.card_is(saved.method_id, kind=CardKind.BUSINESS, network="mastercard")

    assert fake.card_kind_of(saved.method_id) is CardKind.BUSINESS
    assert fake.card_network_of(saved.method_id) == "mastercard"


# --------------------------------------------------------------------------- #
# Hold windows
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("network", "lasts"),
    [
        ("visa", timedelta(days=4, hours=18)),
        ("mastercard", timedelta(days=7)),
    ],
)
async def test_a_hold_made_without_its_player_lasts_its_network_s_window(
    network, lasts
):
    fake, _ = _a_fake()

    payment = await _a_hold(fake, replace(A_CARD, brand=network))
    read = await fake.read_payment(account_id=ACCOUNT, payment_id=payment)

    assert read.status is PaymentStatus.AUTHORISED
    assert read.last_moment == MONDAY + lasts


async def test_a_hold_its_player_confirmed_in_the_app_lasts_seven_days_on_a_visa():
    """Confirmed on the phone, the payment is the player's own — Stripe's
    customer-initiated window, which is 7 days on every network."""

    fake, clock = _a_fake()
    payment = await _a_hold(fake, A_CARD_THAT_DECLINES_LATER)
    clock.move(timedelta(minutes=10))

    fake.phone_confirms_payment(payment, with_card=A_CARD)
    read = await fake.read_payment(account_id=ACCOUNT, payment_id=payment)

    assert read.status is PaymentStatus.AUTHORISED
    assert read.last_moment == MONDAY + timedelta(minutes=10, days=7)


async def test_a_hold_is_taken_at_its_last_moment():
    fake, clock = _a_fake()
    payment = await _a_hold(fake)
    clock.move(timedelta(days=4, hours=18))

    taken = await fake.capture(
        account_id=ACCOUNT, payment_id=payment, idempotency_key="t"
    )

    assert taken.status is PaymentStatus.CAPTURED


async def test_a_capture_after_the_last_moment_is_refused_and_the_hold_has_lapsed():
    fake, clock = _a_fake()
    payment = await _a_hold(fake)
    clock.move(timedelta(days=4, hours=18, seconds=1))

    with pytest.raises(FakeRefusal):
        await fake.capture(account_id=ACCOUNT, payment_id=payment, idempotency_key="t")
    read = await fake.read_payment(account_id=ACCOUNT, payment_id=payment)

    assert read.status is PaymentStatus.CANCELLED
    assert read.last_moment is None
    assert fake.notices[-1].kind == "payment_intent.canceled"


async def test_a_hold_that_lapsed_is_read_cancelled_without_anybody_asking_to_take_it():
    fake, clock = _a_fake()
    payment = await _a_hold(fake, replace(A_CARD, brand="mastercard"))
    clock.move(timedelta(days=7, seconds=1))

    read = await fake.read_payment(account_id=ACCOUNT, payment_id=payment)

    assert read.status is PaymentStatus.CANCELLED


async def test_a_fake_with_no_clock_reports_no_last_moment_and_lets_nothing_lapse():
    """A test's fake is given the clock it needs: one that is not dates
    nothing, as with a payout."""

    fake = FakePayments()

    payment = await _a_hold(fake)
    read = await fake.read_payment(account_id=ACCOUNT, payment_id=payment)

    assert read.last_moment is None


# --------------------------------------------------------------------------- #
# A fee not yet known
# --------------------------------------------------------------------------- #


async def test_a_club_on_its_own_pricing_is_told_its_fee_later():
    fake, _ = _a_fake()
    fake.fees_reported_later.add(ACCOUNT)
    payment = await _a_hold(fake)

    taken = await fake.capture(
        account_id=ACCOUNT, payment_id=payment, idempotency_key="t"
    )
    fake.reports_fee(payment)
    read = await fake.read_payment(account_id=ACCOUNT, payment_id=payment)

    assert taken.status is PaymentStatus.CAPTURED
    assert taken.fee_grosze is None
    assert read.fee_grosze == 1_60


# --------------------------------------------------------------------------- #
# An exact refund
# --------------------------------------------------------------------------- #


async def test_a_refund_gives_back_exactly_what_it_is_asked():
    fake, _ = _a_fake()
    payment = await _a_hold(fake, replace(A_CARD, kind=CardKind.BUSINESS))
    await fake.capture(account_id=ACCOUNT, payment_id=payment, idempotency_key="t")

    refund = await fake.refund(
        account_id=ACCOUNT, payment_id=payment, amount_grosze=38_24, idempotency_key="r"
    )

    assert refund.amount_grosze == 38_24


async def test_a_refund_of_more_than_was_taken_is_refused():
    fake, _ = _a_fake()
    payment = await _a_hold(fake)
    await fake.capture(account_id=ACCOUNT, payment_id=payment, idempotency_key="t")

    with pytest.raises(FakeRefusal):
        await fake.refund(
            account_id=ACCOUNT,
            payment_id=payment,
            amount_grosze=40_01,
            idempotency_key="r",
        )
