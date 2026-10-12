"""``ProposalDirectory`` over the two projections.

**Every live read is bounded by ``now`` as well as by the recorded ending**,
because a proposal past its book-by is over at every instant and the sweep that
records it runs on a cadence (``application/expire_proposals.py``).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import final
from uuid import UUID

from sqlalchemy import ColumnElement, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.matchfit.core import SearchMode
from app.infrastructure.database.stored_time import stored_instant
from app.kernel import Instant, Sport
from app.modules.proposals.domain.ports import LiveYes
from app.modules.proposals.domain.proposal import Ending, Origin
from app.modules.proposals.infrastructure.proposal_models import (
    ProposalORM,
    ProposalPersonORM,
)


def _filling(now: Instant) -> ColumnElement[bool]:
    return and_(ProposalORM.ended.is_(None), ProposalORM.book_by > now)


def _saying_yes(player_id: UUID) -> ColumnElement[bool]:
    return and_(
        ProposalPersonORM.proposal_id == ProposalORM.id,
        ProposalPersonORM.player_id == player_id,
        ProposalPersonORM.answer == "YES",
    )


@final
class SqlAlchemyProposalDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def live_yeses_of(
        self, player_id: UUID, *, now: Instant
    ) -> Sequence[LiveYes]:
        rows = (
            await self._session.scalars(
                select(ProposalORM)
                .join(ProposalPersonORM, _saying_yes(player_id))
                .where(_filling(now))
                .order_by(ProposalORM.start, ProposalORM.id)
            )
        ).all()
        return [
            LiveYes(
                proposal_id=row.id,
                pool_id=row.pool_id,
                sport=Sport(row.sport),
                kind=SearchMode(row.kind),
                club_id=row.club_id,
                start=stored_instant(row.start),
                share_grosze=row.share_grosze,
                book_by=stored_instant(row.book_by),
            )
            for row in rows
        ]

    async def paused_for(self, player_id: UUID, *, now: Instant) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(ProposalORM.id)
                .join(
                    ProposalPersonORM,
                    and_(
                        ProposalPersonORM.proposal_id == ProposalORM.id,
                        ProposalPersonORM.player_id == player_id,
                        ProposalPersonORM.answer == "PAUSED",
                    ),
                )
                .where(_filling(now))
                .order_by(ProposalORM.start, ProposalORM.id)
            )
        ).all()

    async def reopened_for(self, player_id: UUID, *, now: Instant) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(ProposalORM.id)
                .join(
                    ProposalPersonORM,
                    and_(
                        ProposalPersonORM.proposal_id == ProposalORM.id,
                        ProposalPersonORM.player_id == player_id,
                        ProposalPersonORM.answer == "WITHDRAWN",
                    ),
                )
                .where(_filling(now))
                .order_by(ProposalORM.start, ProposalORM.id)
            )
        ).all()

    async def past_book_by(self, *, now: Instant) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(ProposalORM.id)
                .where(
                    ProposalORM.ended.is_(None),
                    ProposalORM.book_by <= now,
                    # A time to pay is ended by its own job, first (#625).
                    ProposalORM.paying_until.is_(None),
                )
                .order_by(ProposalORM.book_by, ProposalORM.id)
            )
        ).all()

    async def paying_past(self, *, now: Instant) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(ProposalORM.id)
                .where(
                    ProposalORM.ended.is_(None),
                    ProposalORM.paying_until <= now,
                )
                .order_by(ProposalORM.paying_until, ProposalORM.id)
            )
        ).all()

    async def paying_for(self, player_id: UUID) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(ProposalORM.id)
                .join(ProposalPersonORM, _saying_yes(player_id))
                .where(
                    ProposalORM.ended.is_(None),
                    ProposalORM.paying_until.is_not(None),
                )
                .order_by(ProposalORM.start, ProposalORM.id)
            )
        ).all()

    async def payment_awaited_of(
        self, player_id: UUID, *, since: Instant | None
    ) -> Sequence[UUID]:
        query = (
            select(ProposalORM.id)
            .join(ProposalPersonORM, _saying_yes(player_id))
            .where(
                ProposalORM.payment_awaited_at.is_not(None),
                or_(
                    ProposalORM.ended.is_(None),
                    # Ended before it was full again: called off, on its card.
                    ProposalORM.ended.in_(
                        (Ending.EXPIRED.value, Ending.COURT_HOUR_LOST.value)
                    ),
                ),
            )
            .order_by(ProposalORM.start, ProposalORM.id)
        )
        if since is not None:
            query = query.where(ProposalORM.start >= since)
        return (await self._session.scalars(query)).all()

    async def filling_in(self, pool_id: UUID, *, now: Instant) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(ProposalORM.id)
                .where(ProposalORM.pool_id == pool_id, _filling(now))
                .order_by(ProposalORM.start, ProposalORM.id)
            )
        ).all()

    async def dealt_to(
        self, player_id: UUID, *, pool_id: UUID, sport: Sport, now: Instant
    ) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(ProposalORM.id)
                .join(
                    ProposalPersonORM,
                    and_(
                        ProposalPersonORM.proposal_id == ProposalORM.id,
                        ProposalPersonORM.player_id == player_id,
                    ),
                )
                .where(
                    ProposalORM.pool_id == pool_id,
                    ProposalORM.sport == sport.value,
                    _filling(now),
                    # Dealt a version — a poster is In without one.
                    ProposalPersonORM.version.is_not(None),
                    or_(
                        ProposalPersonORM.answer.is_(None),
                        ProposalPersonORM.answer == "WITHDRAWN",
                    ),
                )
                .order_by(ProposalORM.start, ProposalORM.id)
            )
        ).all()

    async def live_posts_of(self, poster_id: UUID, *, now: Instant) -> int:
        counted = await self._session.scalar(
            select(func.count())
            .select_from(ProposalORM)
            .join(ProposalPersonORM, _saying_yes(poster_id))
            .where(
                _filling(now),
                ProposalORM.origin == Origin.POST.value,
                ProposalORM.poster_id == poster_id,
            )
        )
        return int(counted or 0)

    async def owed_a_new_card_in(
        self, pool_id: UUID, *, now: Instant
    ) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(ProposalORM.id)
                .where(
                    ProposalORM.pool_id == pool_id,
                    ProposalORM.club_cancelled.is_(True),
                    ProposalORM.start > now,
                )
                .order_by(ProposalORM.start, ProposalORM.id)
            )
        ).all()
