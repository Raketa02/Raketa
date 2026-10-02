"""The Club payout repository: one stream per club per day it is paid for, and
its projection (#548).

The same shape as the seat charge's (``docs/adr/0018``): **its rows are written
by ``save``, in the caller's transaction, and flushed** — the release and the
send are each one transaction, and a game's row is what keeps it from being
paid out twice, so it must meet the primary key before the commit does. A game
another process paid out a moment ago meets it as **a conflict**, the same
answer as the stream's: somebody else got there first.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.events import EventStreamVersionConflict
from app.application.ports import DomainEventPublisher, DomainEventStore
from app.kernel import Instant
from app.modules.payments.domain.club_payout import ClubPayout
from app.modules.payments.domain.events import ClubPayoutDecided
from app.modules.payments.infrastructure.payment_models import (
    ClubPayoutGameORM,
    ClubPayoutORM,
    SeatChargeORM,
)

CLUB_PAYOUT_AGGREGATE = "club_payout"


@final
class EventSourcedClubPayoutRepository:
    """``ClubPayoutRepository`` over ``DomainEventStore``, ``club_payouts`` and
    ``club_payout_games``."""

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

    async def load(self, payout_id: UUID) -> ClubPayout | None:
        stored = await self._event_store.load_stream(
            aggregate_type=CLUB_PAYOUT_AGGREGATE, aggregate_id=payout_id
        )
        if not stored:
            return None
        payout = ClubPayout.from_history(record.event for record in stored)
        self._versions[payout_id] = payout.version
        return payout

    async def save(self, payout: ClubPayout) -> None:
        pending = payout.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=CLUB_PAYOUT_AGGREGATE,
            aggregate_id=payout.payout_id,
            expected_version=self._versions.get(payout.payout_id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        if isinstance(pending[0], ClubPayoutDecided):
            self._session.add(
                ClubPayoutORM(
                    payout_id=payout.payout_id,
                    club_id=payout.club_id,
                    day=payout.day,
                    amount_grosze=payout.amount_grosze,
                    decided_at=payout.decided_at,
                    sent_at=payout.sent_at,
                )
            )
            await self._session.flush()
            self._session.add_all(
                ClubPayoutGameORM(game_id=game_id, payout_id=payout.payout_id)
                for game_id in payout.game_ids
            )
            try:
                await self._session.flush()
            except IntegrityError as carried:
                # Another day's payout, released by another process a moment
                # ago, carried one of these games. The transaction is spent.
                raise EventStreamVersionConflict(
                    f"a game of {payout.payout_id} was paid out already"
                ) from carried
        else:
            await self._session.execute(
                update(ClubPayoutORM)
                .where(ClubPayoutORM.payout_id == payout.payout_id)
                .values(sent_at=payout.sent_at)
            )
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[payout.payout_id] = payout.version

    async def owed(self, *, starting_before: Instant) -> Mapping[UUID, frozenset[UUID]]:
        carried = select(ClubPayoutGameORM.game_id)
        rows = await self._session.execute(
            select(SeatChargeORM.club_id, SeatChargeORM.game_id)
            .where(
                SeatChargeORM.taken_at.is_not(None),
                or_(
                    SeatChargeORM.starts_at.is_(None),
                    SeatChargeORM.starts_at < starting_before,
                ),
                SeatChargeORM.game_id.not_in(carried),
            )
            .distinct()
        )
        owed: dict[UUID, set[UUID]] = {}
        for club_id, game_id in rows.all():
            owed.setdefault(club_id, set()).add(game_id)
        return {club_id: frozenset(games) for club_id, games in owed.items()}

    async def paid_out(self, game_ids: Collection[UUID]) -> frozenset[UUID]:
        if not game_ids:
            return frozenset()
        found = await self._session.scalars(
            select(ClubPayoutGameORM.game_id)
            .join(
                ClubPayoutORM,
                ClubPayoutORM.payout_id == ClubPayoutGameORM.payout_id,
            )
            .where(
                ClubPayoutGameORM.game_id.in_(list(game_ids)),
                ClubPayoutORM.sent_at.is_not(None),
            )
        )
        return frozenset(found.all())
