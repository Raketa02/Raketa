"""What a club payout's decision leaves at the provider: **the payout is made**,
and the desk is told *A payout was sent* (#548; the mechanics §12.6, §16.12;
the screens B9).

**After the commit, from the outbox, and never inline** — the payouts job
records the decision, so a provider that cannot be reached, or a balance that
cannot cover it yet (``PaymentsUnavailable``), leaves the delivery to be tried
again, and the money follows the record rather than the other way round. The
provider's answer and the email are written in the same delivery.

**The key is the payout's own**, so every retry is the same request, and a
payout the provider already made answers it again. A payout the delivery finds
already sent asks nothing.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.events import DeliveryContext
from app.application.ports.mail import MailQueue
from app.kernel import Clock, instant
from app.modules.payments.application.payout_emails import payout_sent_email
from app.modules.payments.domain.events import ClubPayoutDecided
from app.modules.payments.domain.ports import ClubPayoutRepository, Sellers
from app.modules.payments.domain.provider import PaymentProvider


def payout_key(payout_id: UUID) -> str:
    """One payout per decision, ever: a retry is the same request."""

    return f"rakieta-payout-{payout_id}"


@final
class SendClubPayout:
    def __init__(
        self,
        *,
        payouts: ClubPayoutRepository,
        sellers: Sellers,
        provider: PaymentProvider,
        mail: MailQueue,
        clock: Clock,
        money_page: str,
    ) -> None:
        self._payouts = payouts
        self._sellers = sellers
        self._provider = provider
        self._mail = mail
        self._clock = clock
        self._money_page = money_page

    async def __call__(
        self, event: ClubPayoutDecided, context: DeliveryContext
    ) -> None:
        payout = await self._payouts.load(event.payout_id)
        if payout is None or payout.is_sent:
            return
        sent = await self._provider.pay_out(
            payout.account_id,
            amount_grosze=payout.amount_grosze,
            description=f"Rakieta · games over by {payout.day.day} {payout.day:%B %Y}",
            metadata={"rakieta_payout": str(payout.payout_id)},
            idempotency_key=payout_key(payout.payout_id),
        )
        now = instant(self._clock.now())
        payout.sent(sent, at=now)
        await self._payouts.save(payout)
        seller = (await self._sellers.of([payout.club_id])).get(payout.club_id)
        if seller is None or seller.email is None:
            return
        await self._mail.enqueue(
            payout_sent_email(
                to=seller.email,
                club=seller.name,
                amount_grosze=payout.amount_grosze,
                games=len(payout.game_ids),
                day=payout.day,
                arrives_at=sent.arrives_at,
                link=self._money_page,
            ),
            at=now,
        )
