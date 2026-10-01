"""What the fill's verdict leaves at the provider: **a taken hold is captured,
a released one cancelled** (``docs/adr/0190`` §4; the mechanics Appendix A).

**After the commit, from the outbox, and never inline** — the fill records the
verdict with the booking, so a provider that cannot be reached leaves the
delivery to be tried again, and the money follows the record rather than the
other way round. The provider's answer is recorded on the charge in the same
delivery, so a receipt reads *paid* the moment the money is.

**The key is the charge's own**, so every retry is the same request, and a
capture or a cancellation the provider already made answers it again. A charge
the delivery finds already settled — a notice got there first — asks nothing.
A released charge that never was a payment — terms to accept again, or no
method — has nothing at the provider to cancel, and is settled at once.
"""

from __future__ import annotations

from typing import final

from app.application.events import DeliveryContext
from app.kernel import Clock, instant
from app.modules.payments.domain.events import SeatChargeReleased, SeatChargeTaken
from app.modules.payments.domain.ports import SeatChargeRepository
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.payments.domain.seat_charge import SeatChargeStatus


def capture_key(charge_id: object) -> str:
    return f"raketa-capture-{charge_id}"


def cancel_seat_key(charge_id: object) -> str:
    return f"raketa-cancel-seat-{charge_id}"


@final
class SettleSeatCharges:
    def __init__(
        self,
        *,
        charges: SeatChargeRepository,
        provider: PaymentProvider,
        clock: Clock,
    ) -> None:
        self._charges = charges
        self._provider = provider
        self._clock = clock

    async def __call__(
        self, event: SeatChargeTaken | SeatChargeReleased, context: DeliveryContext
    ) -> None:
        charge = await self._charges.load(event.charge_id)
        if charge is None:
            return
        now = instant(self._clock.now())
        if charge.status is SeatChargeStatus.TAKING:
            assert charge.payment_id is not None
            await self._provider.capture(
                account_id=charge.account_id,
                payment_id=charge.payment_id,
                idempotency_key=capture_key(charge.charge_id),
            )
            charge.captured(at=now)
        elif charge.status is SeatChargeStatus.RELEASING:
            if charge.payment_id is not None:
                await self._provider.cancel(
                    account_id=charge.account_id,
                    payment_id=charge.payment_id,
                    idempotency_key=cancel_seat_key(charge.charge_id),
                )
            charge.cancelled(at=now)
        else:
            return
        await self._charges.save(charge)
