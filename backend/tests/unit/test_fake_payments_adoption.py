"""The fake provider answers for a payment **another process** made (#541,
#544): a seed run fills games through its own fake, and a laptop's server
reloads, so the outbox that captures a seat — or gives a leaver's share back —
may reach a fake that never held it. It must still answer as the provider
would, for the amount the payment was made for.
"""

from __future__ import annotations

from app.modules.payments.domain.entered_cards import A_CARD
from app.modules.payments.domain.provider import PaymentStatus
from app.modules.payments.infrastructure.fake_payments import FakePayments
from app.shared.ids import new_uuid


async def _a_captured_share(fake: FakePayments, *, account: str) -> str:
    """A 30 zł share held and taken through ``fake``: its payment's id."""

    customer = await fake.open_customer(player_id=new_uuid(), idempotency_key="c")
    setup = await fake.start_setup(
        customer_id=customer, player_id=new_uuid(), idempotency_key="s"
    )
    fake.phone_enters(setup.setup_id, A_CARD)
    card = (await fake.read_setup(setup.setup_id)).card
    assert card is not None
    clone = await fake.clone_method(
        customer_id=customer,
        method_id=card.method_id,
        account_id=account,
        idempotency_key="k",
    )
    held = await fake.authorise(
        account_id=account,
        method_id=clone,
        amount_grosze=30_00,
        description="Padel",
        metadata={},
        idempotency_key="h",
    )
    await fake.capture(
        account_id=account, payment_id=held.payment_id, idempotency_key="t"
    )
    return held.payment_id


async def test_a_share_another_process_took_is_refunded_for_what_it_was():
    """Given back as a payment taken, since Raketa refunds only a share it
    recorded paid — and never more than its id says it was for."""
    account = "acct_fake_club"
    payment_id = await _a_captured_share(FakePayments(), account=account)
    after_a_reload = FakePayments()

    refund = await after_a_reload.refund(
        account_id=account,
        payment_id=payment_id,
        amount_grosze=28_55,
        idempotency_key="r",
    )

    assert refund.amount_grosze == 28_55
    read = await after_a_reload.read_payment(account_id=account, payment_id=payment_id)
    assert read.status is PaymentStatus.CAPTURED
