"""The fake provider's controls for the games test console (#591;
``docs/adr/0194`` §2).

**The notices it would have sent.** Stripe tells Raketa that a payment moved by
webhook, and the fake moves payments without one — so it records, in order, the
notice Stripe would have sent for every move: what the console replays, twice or
out of order, through the webhook's own handling.

**Refunds that wait.** The fake gives a refund the moment it is asked; told to
wait, it answers as a provider that has not given it yet — the outbox asks again
— until the console lets that payment's refund through.
"""

from __future__ import annotations

import pytest

from app.modules.payments.domain.entered_cards import (
    A_CARD,
    A_CARD_THAT_DECLINES_LATER,
    CardBehaviour,
    EnteredCard,
)
from app.modules.payments.domain.errors import PaymentsUnavailable
from app.modules.payments.domain.provider import PaymentStatus
from app.modules.payments.infrastructure.fake_payments import (
    NOTICE_KINDS,
    FakePayments,
)
from app.modules.payments.infrastructure.stripe_notices import SEAT_PAYMENT_KINDS
from app.shared.ids import new_uuid

ACCOUNT = "acct_fake_club"


async def _a_saved_card(fake: FakePayments, card: EnteredCard = A_CARD) -> str:
    customer = await fake.open_customer(player_id=new_uuid(), idempotency_key="c")
    setup = await fake.start_setup(
        customer_id=customer, player_id=new_uuid(), idempotency_key="s"
    )
    fake.phone_enters(setup.setup_id, card)
    saved = (await fake.read_setup(setup.setup_id)).card
    assert saved is not None
    return saved.method_id


async def _a_hold(fake: FakePayments, method_id: str, *, key: str = "h") -> str:
    clone = await fake.clone_method(
        customer_id="cus",
        method_id=method_id,
        account_id=ACCOUNT,
        idempotency_key=f"clone-{key}",
    )
    held = await fake.authorise(
        account_id=ACCOUNT,
        method_id=clone,
        amount_grosze=30_00,
        description="Padel",
        metadata={},
        idempotency_key=key,
    )
    return held.payment_id


def _sent(fake: FakePayments) -> list[tuple[str, str, PaymentStatus]]:
    return [(sent.notice.payment_id, sent.kind, sent.status) for sent in fake.notices]


# --------------------------------------------------------------------------- #
# The notices it would have sent
# --------------------------------------------------------------------------- #


async def test_a_hold_then_its_capture_are_two_notices_in_order():
    fake = FakePayments()
    payment = await _a_hold(fake, await _a_saved_card(fake))

    await fake.capture(account_id=ACCOUNT, payment_id=payment, idempotency_key="t")

    assert _sent(fake) == [
        (payment, "payment_intent.amount_capturable_updated", PaymentStatus.AUTHORISED),
        (payment, "payment_intent.succeeded", PaymentStatus.CAPTURED),
    ]
    first, second = fake.notices
    assert first.notice.account_id == ACCOUNT
    assert first.notice.notice_id != second.notice.notice_id


async def test_a_hold_let_go_is_a_cancellation_notice():
    fake = FakePayments()
    payment = await _a_hold(fake, await _a_saved_card(fake))

    await fake.cancel(account_id=ACCOUNT, payment_id=payment, idempotency_key="x")

    assert [kind for _, kind, _ in _sent(fake)] == [
        "payment_intent.amount_capturable_updated",
        "payment_intent.canceled",
    ]


async def test_a_declined_payment_and_its_confirmation_are_notices_too():
    fake = FakePayments()
    payment = await _a_hold(fake, await _a_saved_card(fake, A_CARD_THAT_DECLINES_LATER))

    fake.phone_confirms_payment(payment, with_card=A_CARD)

    assert _sent(fake) == [
        (payment, "payment_intent.payment_failed", PaymentStatus.DECLINED),
        (payment, "payment_intent.amount_capturable_updated", PaymentStatus.AUTHORISED),
    ]


async def test_asking_again_under_the_same_key_sends_nothing_twice():
    fake = FakePayments()
    method = await _a_saved_card(fake)
    payment = await _a_hold(fake, method)

    assert await _a_hold(fake, method) == payment
    await fake.capture(account_id=ACCOUNT, payment_id=payment, idempotency_key="t")
    await fake.capture(account_id=ACCOUNT, payment_id=payment, idempotency_key="t")

    assert len(fake.notices) == 2


def test_every_notice_it_records_is_of_a_kind_stripe_notices_reads():
    """The kinds are Stripe's words, spelled twice — here and in the reader —
    so a kind the reader would not take is a replay that silently does
    nothing."""

    assert set(NOTICE_KINDS.values()) <= SEAT_PAYMENT_KINDS


# --------------------------------------------------------------------------- #
# A saved card, steered
# --------------------------------------------------------------------------- #


async def test_a_card_s_behaviour_is_read_as_it_was_last_set():
    fake = FakePayments()
    method = await _a_saved_card(fake)
    assert fake.card_behaviour_of(method) is CardBehaviour.SUCCEEDS

    fake.card_behaves(method, CardBehaviour.DECLINES_PAYMENTS)

    assert fake.card_behaviour_of(method) is CardBehaviour.DECLINES_PAYMENTS
    payment = await _a_hold(fake, method)
    assert fake.notices[-1].status is PaymentStatus.DECLINED
    assert fake.notices[-1].notice.payment_id == payment


async def test_a_card_another_process_saved_reads_as_the_card_every_seed_saves():
    assert FakePayments().card_behaviour_of("pm_seeded_elsewhere") is (
        CardBehaviour.SUCCEEDS
    )


# --------------------------------------------------------------------------- #
# Refunds that wait
# --------------------------------------------------------------------------- #


async def _a_captured_share(
    fake: FakePayments, method_id: str | None = None, *, key: str = "h"
) -> str:
    method = method_id or await _a_saved_card(fake)
    payment = await _a_hold(fake, method, key=key)
    await fake.capture(
        account_id=ACCOUNT, payment_id=payment, idempotency_key=f"take-{key}"
    )
    return payment


async def test_a_refund_is_given_at_once_unless_refunds_wait():
    fake = FakePayments()
    payment = await _a_captured_share(fake)

    refund = await fake.refund(
        account_id=ACCOUNT, payment_id=payment, amount_grosze=30_00, idempotency_key="r"
    )

    assert refund.amount_grosze == 30_00


async def test_a_refund_that_waits_is_not_given_until_it_is_let_through():
    fake = FakePayments()
    payment = await _a_captured_share(fake)
    fake.refunds_wait = True

    with pytest.raises(PaymentsUnavailable):
        await fake.refund(
            account_id=ACCOUNT,
            payment_id=payment,
            amount_grosze=30_00,
            idempotency_key="r",
        )
    fake.gives_refund(payment)
    refund = await fake.refund(
        account_id=ACCOUNT, payment_id=payment, amount_grosze=30_00, idempotency_key="r"
    )

    assert refund.amount_grosze == 30_00


async def test_letting_refunds_go_again_gives_every_one_asked_for():
    fake = FakePayments()
    payment = await _a_captured_share(fake)
    fake.refunds_wait = True
    with pytest.raises(PaymentsUnavailable):
        await fake.refund(
            account_id=ACCOUNT,
            payment_id=payment,
            amount_grosze=30_00,
            idempotency_key="r",
        )

    fake.refunds_wait = False
    refund = await fake.refund(
        account_id=ACCOUNT, payment_id=payment, amount_grosze=30_00, idempotency_key="r"
    )

    assert refund.amount_grosze == 30_00
