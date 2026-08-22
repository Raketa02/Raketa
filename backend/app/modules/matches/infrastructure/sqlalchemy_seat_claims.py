"""Is this player already buying a seat — anywhere.

The one question about seat claims that no single match can answer, and
therefore the one that needs a port of its own. ADR-0081 fixes **one live claim
per player**, so nobody parks three seats across three matches while deciding;
the aggregate can see only its own claims, and the cross-match half is a narrow
indexed read that wants neither a whole match nor a whole claim.

Same shape as ``SqlAlchemyMatchSchedule`` beside it, and for the same reason:
one table, two ports, two questions of completely different width.

**It is a query and never a write.** *Live* is composed — unended **and** not
yet expired — so a player whose last claim ran out is free the instant it did,
without waiting for a scheduled look to write the receipt. That is why the
partial index it rides is `ended_at IS NULL` and this ``WHERE`` says more: the
index over-covers by the rows a reaper has not reached yet, which costs a page,
where a *unique* index over the same predicate would have to spell *live* as
*unended* and would refuse a player on the strength of a row nobody had closed.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Instant

from app.modules.matches.infrastructure.sqlalchemy_match_models import (
    MatchSeatClaimORM,
)


class SqlAlchemySeatClaims:
    """The cross-match claim read, and nothing else."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def live_for(self, player_id: UUID, *, at: Instant) -> UUID | None:
        """The match this player is already buying a seat in, or nothing.

        Ordered and limited rather than fetched whole, so the answer is one row
        however many claims she has ever made. The order is total — the soonest
        deadline, then the id — which matters only for determinism: the rule is
        that there is at most one, and if a race ever produced two, the one
        about to expire is the one worth naming.
        """

        row = await self._session.execute(
            select(MatchSeatClaimORM.match_id)
            .where(
                MatchSeatClaimORM.player_id == player_id,
                MatchSeatClaimORM.ended_at.is_(None),
                MatchSeatClaimORM.expires_at > at,
            )
            .order_by(MatchSeatClaimORM.expires_at, MatchSeatClaimORM.id)
            .limit(1)
        )
        return row.scalars().one_or_none()
