"""What a share's settling asks of the provider (#544, #548; ADR-0190's
2026-10-10 amendment).

**The caller computes a refund.** The provider is asked for an exact amount:
the whole share where the refund is in full, and the share less **the fee kept
on that payment** where the fee is withheld — never an estimate. A refund whose
fee is not yet known waits: the delivery fails, the outbox asks again, and once
the provider reports the fee it is recorded on the charge and the refund made.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.kernel import Sport, instant
from app.modules.payments.application.handlers.settle_seat_charges import (
    SettleSeatCharges,
)
from app.modules.payments.domain.entered_cards import A_CARD, CardKind, EnteredCard
from app.modules.payments.domain.errors import PaymentsUnavailable
from app.modules.payments.domain.seat_charge import SeatCharge
from app.modules.payments.infrastructure.fake_payments import FakePayments
from app.shared.domain import DomainEvent
from app.shared.ids import new_uuid
from tests.unit.fake_clock import MovableClock

ACCOUNT = "acct_fake_club"
AT = instant(datetime(2026, 10, 12, 9, tzinfo=timezone.utc))
GAME = instant(datetime(2026, 10, 15, 17, tzinfo=timezone.utc))


class InMemoryCharges:
    """``SeatChargeRepository``, as far as settling reads it: each charge's
    stream, folded afresh on every load."""

    def __init__(self) -> None:
        self._streams: dict[UUID, list[DomainEvent]] = {}

    async def load(self, charge_id: UUID) -> SeatCharge | None:
        stream = self._streams.get(charge_id)
        return None if stream is None else SeatCharge.from_history(stream)

    async def save(self, charge: SeatCharge) -> None:
        self._streams.setdefault(charge.charge_id, []).extend(charge.pull_events())


async def _a_share_taken(
    fake: FakePayments, charges: InMemoryCharges, card: EnteredCard = A_CARD
) -> UUID:
    """A 40 zł share held on ``card`` and taken: its charge's id."""

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
        amount_grosze=40_00,
        description="Padel",
        metadata={},
        idempotency_key="h",
    )
    charge = SeatCharge.held(
        charge_id=uuid4(),
        player_id=uuid4(),
        game_id=uuid4(),
        club_id=uuid4(),
        account_id=ACCOUNT,
        payment=held,
        sport=Sport.PADEL,
        starts_at=GAME,
        at=AT,
    )
    charge.take(booking_id=charge.game_id, at=AT)
    await charges.save(charge)
    return charge.charge_id


async def _decided(
    charges: InMemoryCharges, charge_id: UUID, *, withhold_fee: bool
) -> None:
    charge = await charges.load(charge_id)
    assert charge is not None
    charge.refund(withhold_fee=withhold_fee, at=AT)
    await charges.save(charge)


def _the_world() -> tuple[FakePayments, InMemoryCharges, SettleSeatCharges]:
    clock = MovableClock(AT)
    fake = FakePayments(clock=clock)
    charges = InMemoryCharges()
    return fake, charges, SettleSeatCharges(charges=charges, provider=fake, clock=clock)


async def test_a_refund_in_full_asks_for_the_whole_share():
    fake, charges, settle = _the_world()
    charge_id = await _a_share_taken(fake, charges)
    await settle.settle(charge_id)
    await _decided(charges, charge_id, withhold_fee=False)

    await settle.settle(charge_id)

    (asked,) = fake.called("refund")
    assert asked.arguments["amount_grosze"] == 40_00
    charge = await charges.load(charge_id)
    assert charge is not None and charge.refund_given is not None
    assert (
        charge.refund_given.amount_grosze,
        charge.refund_given.fee_withheld_grosze,
    ) == (
        40_00,
        0,
    )


@pytest.mark.parametrize(
    ("kind", "given_back"),
    [
        (CardKind.PERSONAL_EU, 38_40),
        (CardKind.BUSINESS, 38_24),
        (CardKind.OUTSIDE_EUROPE, 37_70),
    ],
)
async def test_a_refund_less_the_fee_withholds_exactly_the_fee_kept_on_that_payment(
    kind, given_back
):
    fake, charges, settle = _the_world()
    charge_id = await _a_share_taken(fake, charges, replace(A_CARD, kind=kind))
    await settle.settle(charge_id)
    await _decided(charges, charge_id, withhold_fee=True)

    await settle.settle(charge_id)

    (asked,) = fake.called("refund")
    assert asked.arguments["amount_grosze"] == given_back
    charge = await charges.load(charge_id)
    assert charge is not None and charge.refund_given is not None
    assert charge.refund_given.fee_withheld_grosze == 40_00 - given_back


async def test_a_refund_whose_fee_is_not_yet_known_waits_until_it_is_reported():
    fake, charges, settle = _the_world()
    fake.fees_reported_later.add(ACCOUNT)
    charge_id = await _a_share_taken(fake, charges, replace(A_CARD, kind=CardKind.UK))
    await settle.settle(charge_id)
    await _decided(charges, charge_id, withhold_fee=True)

    with pytest.raises(PaymentsUnavailable):
        await settle.settle(charge_id)
    assert fake.called("refund") == []

    charge = await charges.load(charge_id)
    assert charge is not None and charge.payment_id is not None
    fake.reports_fee(charge.payment_id)
    await settle.settle(charge_id)

    (asked,) = fake.called("refund")
    assert asked.arguments["amount_grosze"] == 38_00
    settled = await charges.load(charge_id)
    assert settled is not None and settled.fee_taken_grosze == 2_00
    assert settled.settled
