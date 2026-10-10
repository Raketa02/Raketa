"""The Seat charge repository: one stream per charge, and its row.

The same shape as the other aggregate repositories (``docs/adr/0018``), and,
like a proposal's, **its projection is written by ``save``, in the caller's
transaction, and flushed** — the fill reads a game's charges back after saving
some of them in the same act, and a session that does not autoflush would
otherwise answer without them.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import final
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.kernel import Instant
from app.modules.payments.domain.events import (
    SeatChargeAuthorised,
    SeatChargeFailed,
)
from app.modules.payments.domain.seat_charge import SeatCharge, SeatChargeStatus
from app.modules.payments.infrastructure.payment_models import SeatChargeORM

SEAT_CHARGE_AGGREGATE = "seat_charge"


@final
class EventSourcedSeatChargeRepository:
    """``SeatChargeRepository`` over ``DomainEventStore`` and ``seat_charges``."""

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
        self._versions: dict[UUID, int] = {}

    async def load(self, charge_id: UUID) -> SeatCharge | None:
        stored = await self._event_store.load_stream(
            aggregate_type=SEAT_CHARGE_AGGREGATE, aggregate_id=charge_id
        )
        if not stored:
            return None
        charge = SeatCharge.from_history(record.event for record in stored)
        self._versions[charge_id] = charge.version
        return charge

    async def save(self, charge: SeatCharge) -> None:
        pending = charge.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=SEAT_CHARGE_AGGREGATE,
            aggregate_id=charge.charge_id,
            expected_version=self._versions.get(charge.charge_id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        if isinstance(pending[0], (SeatChargeAuthorised, SeatChargeFailed)):
            self._session.add(
                SeatChargeORM(
                    charge_id=charge.charge_id,
                    player_id=charge.player_id,
                    game_id=charge.game_id,
                    club_id=charge.club_id,
                    payment_id=charge.payment_id,
                    amount_grosze=charge.amount_grosze,
                    status=charge.status.value,
                    opened_at=charge.opened_at,
                    taken_at=charge.taken_at,
                    starts_at=charge.starts_at,
                    held_until=charge.held_until,
                )
            )
            await self._session.flush()
        else:
            await self._session.flush()
            await self._session.execute(
                update(SeatChargeORM)
                .where(SeatChargeORM.charge_id == charge.charge_id)
                .values(
                    status=charge.status.value,
                    taken_at=charge.taken_at,
                    held_until=charge.held_until,
                )
            )
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[charge.charge_id] = charge.version

    async def of_game(self, game_id: UUID) -> Sequence[SeatCharge]:
        return await self._loaded(
            select(SeatChargeORM.charge_id)
            .where(SeatChargeORM.game_id == game_id)
            .order_by(SeatChargeORM.opened_at, SeatChargeORM.charge_id)
        )

    async def by_payment(self, payment_id: str) -> SeatCharge | None:
        found = await self._session.scalar(
            select(SeatChargeORM.charge_id).where(
                SeatChargeORM.payment_id == payment_id
            )
        )
        return None if found is None else await self.load(found)

    async def games_held_until(self, moment: Instant) -> Sequence[UUID]:
        ids = await self._session.scalars(
            select(SeatChargeORM.game_id)
            .where(
                SeatChargeORM.status == SeatChargeStatus.HELD.value,
                SeatChargeORM.held_until <= moment,
            )
            .group_by(SeatChargeORM.game_id)
            .order_by(func.min(SeatChargeORM.held_until), SeatChargeORM.game_id)
        )
        return tuple(ids.all())

    async def receipts_of(self, player_id: UUID) -> Sequence[SeatCharge]:
        return await self._loaded(
            select(SeatChargeORM.charge_id)
            .where(
                SeatChargeORM.player_id == player_id,
                or_(
                    SeatChargeORM.taken_at.is_not(None),
                    # Held for a booked game, and let go untaken (#641): which
                    # of these the stream says was let go is the read's to ask.
                    and_(
                        SeatChargeORM.held_until.is_not(None),
                        SeatChargeORM.status.in_(
                            (
                                SeatChargeStatus.RELEASING.value,
                                SeatChargeStatus.CANCELLED.value,
                            )
                        ),
                    ),
                ),
            )
            .order_by(
                SeatChargeORM.taken_at.desc().nulls_last(), SeatChargeORM.charge_id
            )
        )

    async def _loaded(self, ids_query) -> list[SeatCharge]:  # type: ignore[no-untyped-def]
        charges: list[SeatCharge] = []
        for charge_id in (await self._session.scalars(ids_query)).all():
            charge = await self.load(charge_id)
            if charge is not None:
                charges.append(charge)
        return charges
