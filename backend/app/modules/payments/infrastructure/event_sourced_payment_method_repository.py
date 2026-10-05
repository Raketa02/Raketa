"""The Payment method repository: one stream per player, and the customer row.

The same shape as the other aggregate repositories — the aggregate type spelled
once, state rebuilt by replay, the version remembered from the load and expected
by the append (``docs/adr/0018``).

**Filed under the player's own id**, so *this player's method* is a stream read.
**``load`` answers an unwritten aggregate rather than ``None``**, as the Plan's
and the Club courts' do: a player who never opened the setup has no method.

**``save`` writes the customer row in the caller's transaction** the first time
a player's stream names a customer, so a notice about that customer finds the
player the moment the setup that opened it commits.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.payments.domain.events import PaymentSetupStarted
from app.modules.payments.domain.payment_method import PaymentMethod
from app.modules.payments.infrastructure.payment_models import PaymentCustomerORM

PAYMENT_METHOD_AGGREGATE = "payment_method"


@final
class EventSourcedPaymentMethodRepository:
    """``PaymentMethodRepository`` over ``DomainEventStore``."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._session = session
        self._event_store = event_store
        self._events = events
        # Player id -> the stream version this unit of work has seen, and the
        # customer the stream named then; zero and ``None`` for a player with no
        # stream yet.
        self._versions: dict[UUID, int] = {}
        self._customers: dict[UUID, str | None] = {}

    async def load(self, player_id: UUID) -> PaymentMethod:
        stored = await self._event_store.load_stream(
            aggregate_type=PAYMENT_METHOD_AGGREGATE, aggregate_id=player_id
        )
        payment_method = PaymentMethod.from_history(
            player_id, (record.event for record in stored)
        )
        self._versions[player_id] = payment_method.version
        self._customers[player_id] = payment_method.customer_id
        return payment_method

    async def save(self, payment_method: PaymentMethod) -> None:
        pending = payment_method.pull_events()
        if not pending:
            return
        player_id = payment_method.player_id
        await self._event_store.append(
            aggregate_type=PAYMENT_METHOD_AGGREGATE,
            aggregate_id=player_id,
            expected_version=self._versions.get(player_id, 0),
            events=pending,
        )
        opened = next(
            (
                event.customer_id
                for event in pending
                if isinstance(event, PaymentSetupStarted)
            ),
            None,
        )
        if opened is not None and self._customers.get(player_id) is None:
            self._session.add(
                PaymentCustomerORM(customer_id=opened, player_id=player_id)
            )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[player_id] = payment_method.version
        self._customers[player_id] = payment_method.customer_id

    async def player_of_customer(self, customer_id: str) -> UUID | None:
        return await self._session.scalar(
            select(PaymentCustomerORM.player_id).where(
                PaymentCustomerORM.customer_id == customer_id
            )
        )
