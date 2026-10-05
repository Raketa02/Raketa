"""Reading and removing the saved payment method (the screens A7.3, state B)."""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.payments.domain.errors import (
    PaymentMethodInUse,
    PaymentMethodNotFound,
)
from app.modules.payments.domain.payment_method import PaymentMethod
from app.modules.payments.domain.ports import (
    PaymentCommitments,
    PaymentMethodRepository,
)


class ReadPaymentMethod:
    """The player's method as their stream tells it: the card, and whether the
    terms wait to be accepted again."""

    def __init__(self, *, methods: PaymentMethodRepository) -> None:
        self._methods = methods

    async def execute(self, player_id: UUID) -> PaymentMethod:
        return await self._methods.load(player_id)


class RemovePaymentMethod:
    """*Remove this method* — refused while anything could still be charged to
    it: a live yes, or a booked game still ahead (the mechanics §12.5, Q83).
    Once recorded, the card is released at the provider by a handler."""

    def __init__(
        self,
        *,
        methods: PaymentMethodRepository,
        commitments: PaymentCommitments,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._methods = methods
        self._commitments = commitments
        self._uow = uow
        self._clock = clock

    async def execute(self, player_id: UUID) -> None:
        now = self._clock.now()
        payment_method = await self._methods.load(player_id)
        if payment_method.method is None:
            raise PaymentMethodNotFound()
        commitments = await self._commitments.of(player_id, at=now)
        if commitments.any:
            raise PaymentMethodInUse(
                live_yeses=commitments.live_yeses,
                upcoming_games=commitments.upcoming_games,
            )
        payment_method.remove(at=now)
        await self._methods.save(payment_method)
        await self._uow.commit()
