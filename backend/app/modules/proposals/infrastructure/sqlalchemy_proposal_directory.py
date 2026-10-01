"""``ProposalDirectory`` over the two projections.

**Every live read is bounded by ``now`` as well as by the recorded ending**,
because a proposal past its book-by is over at every instant and the sweep that
records it runs on a cadence (``application/expire_proposals.py``) — **except a
game waiting for its club** (#543), which filled in time and which only its
club's answer ends.
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
from app.modules.proposals.domain.proposal import Ending
from app.modules.proposals.infrastructure.proposal_models import (
    ProposalORM,
    ProposalPersonORM,
)


def _filling(now: Instant) -> ColumnElement[bool]:
    return and_(
        ProposalORM.ended.is_(None),
        or_(ProposalORM.book_by > now, ProposalORM.waiting_for_the_club.is_(True)),
    )


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

    async def live_yes_count(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> int:
        counted = await self._session.scalar(
            select(func.count())
            .select_from(ProposalORM)
            .join(ProposalPersonORM, _saying_yes(player_id))
            .where(_filling(now), ProposalORM.sport == sport.value)
        )
        return int(counted or 0)

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
                    ProposalORM.waiting_for_the_club.is_(False),
                )
                .order_by(ProposalORM.book_by, ProposalORM.id)
            )
        ).all()

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

    async def turned_down_in(self, pool_id: UUID, *, now: Instant) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(ProposalORM.id)
                .where(
                    ProposalORM.pool_id == pool_id,
                    ProposalORM.ended == Ending.TURNED_DOWN.value,
                    ProposalORM.start > now,
                )
                .order_by(ProposalORM.start, ProposalORM.id)
            )
        ).all()
