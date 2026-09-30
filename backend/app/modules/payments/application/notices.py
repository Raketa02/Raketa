"""Reading a notice the payment provider sent, once (``domain/notices.py``).

**The inbox row and whatever the notice moved commit together**, so a notice is
either read and acted on or neither — and a second delivery finds the row and
does nothing. A notice about a customer nobody here opened, a setup that is not
the one open, or a card that is not the saved one is read and changes nothing:
the provider has told Raketa something Raketa has no stake in, and a retry
would tell it again for three days.
"""

from __future__ import annotations

import logging

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant
from app.modules.payments.application.setup import saved_from
from app.modules.payments.domain.notices import (
    CardUpdatedByBank,
    Notice,
    SetupSucceeded,
    Unheeded,
)
from app.modules.payments.domain.ports import NoticeInbox, PaymentMethodRepository
from app.modules.payments.domain.provider import PaymentProvider

logger = logging.getLogger(__name__)


def kind_of(notice: Notice) -> str:
    """The name a notice is filed under in the inbox."""

    match notice:
        case SetupSucceeded():
            return "setup_succeeded"
        case CardUpdatedByBank():
            return "card_updated_by_bank"
        case Unheeded():
            return notice.kind


class ReceivePaymentNotice:
    def __init__(
        self,
        *,
        inbox: NoticeInbox,
        methods: PaymentMethodRepository,
        provider: PaymentProvider,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._inbox = inbox
        self._methods = methods
        self._provider = provider
        self._uow = uow
        self._clock = clock

    async def execute(self, notice: Notice) -> bool:
        """Act on ``notice`` and answer ``True``, or answer ``False`` for one
        read before."""

        now = self._clock.now()
        if not await self._inbox.first_reading(
            notice.notice_id, kind=kind_of(notice), at=now
        ):
            return False
        match notice:
            case SetupSucceeded():
                await self._setup_succeeded(notice, at=now)
            case CardUpdatedByBank():
                await self._card_updated(notice, at=now)
            case Unheeded():
                pass
        await self._uow.commit()
        return True

    async def _setup_succeeded(self, notice: SetupSucceeded, *, at: Instant) -> None:
        player_id = await self._methods.player_of_customer(notice.customer_id)
        if player_id is None:
            return
        payment_method = await self._methods.load(player_id)
        setup = payment_method.setup
        if setup is None or setup.setup_id != notice.setup_id or setup.terms is None:
            # Saved already, abandoned for a later setup, or — which the secret
            # being handed out only by the acceptance should make impossible —
            # confirmed without the terms. None of them is saved from here.
            logger.info(
                "payments.notice.setup_not_open",
                extra={"notice_id": notice.notice_id, "player_id": str(player_id)},
            )
            return
        reading = await self._provider.read_setup(notice.setup_id)
        saved_from(payment_method, reading, at=at)
        await self._methods.save(payment_method)

    async def _card_updated(self, notice: CardUpdatedByBank, *, at: Instant) -> None:
        player_id = await self._methods.player_of_customer(notice.customer_id)
        if player_id is None:
            return
        payment_method = await self._methods.load(player_id)
        saved = payment_method.method
        if saved is None or saved.method_id != notice.method_id:
            return
        # The card as it stands, never as the notice said: a bank that moved a
        # card and moved it back sends two notices in either order.
        card = await self._provider.read_card(notice.method_id)
        payment_method.bank_updated(card, at=at)
        await self._methods.save(payment_method)
