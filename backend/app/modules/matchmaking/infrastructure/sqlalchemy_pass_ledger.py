"""``PassLedger`` over SQLAlchemy. **It adds rows and it never commits.**

The transaction boundary is the command's decision, exactly as it is for the
interest ledger and the search store beside it: a pass and the read that proved
its origin key belong to one request.

**There is no delete and no update here.** A pass record does not expire
(``the-engine.md`` §12) and nothing but erasure will ever remove one, so a method
for either would be a method somebody reaches for.

**Nothing here can answer a question a route could ask.** No list, no count, no
*who passed on me*: the port declares two methods and this implements exactly
those, so *no route ever returns a pass* is a property of the shapes that exist
rather than of the routes that happen to have been written.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Collection, Mapping
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Sport
from app.modules.matchmaking.domain.passes import Pass
from app.modules.matchmaking.infrastructure.pass_model import PassORM
from app.shared.ids import new_uuid


class SqlAlchemyPassLedger:
    """The durable record of every pass, over the caller's own session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, passed_on: Pass) -> None:
        """Append one pass. The caller commits.

        The id is minted here rather than carried on :class:`Pass`, because it is
        a storage identity and nothing in the domain, in a response or in a
        falsifier ever names it: what identifies a pass to anybody who asks is
        the pair, the moment and the origin.
        """

        self._session.add(
            PassORM(
                id=new_uuid(),
                passer_id=passed_on.passer_id,
                passed_id=passed_on.passed_id,
                sport=passed_on.sport.value,
                passed_at=passed_on.at,
                origin_search_id=passed_on.origin.search_id,
                origin_position=passed_on.origin.position,
            )
        )
        await self._session.flush()

    async def last_passed_at(
        self, *, passer_id: UUID, sport: Sport, candidate_ids: Collection[UUID]
    ) -> Mapping[UUID, datetime]:
        """When the passer last passed on each of these, in this sport.

        Unbounded by time on purpose: the record does not expire, and *when was
        this pair passed* is the question the suppression cache cannot answer
        once its key is gone. An empty population short-circuits — an ``IN ()``
        is a query asking the database about nobody.

        The **latest** of them, grouped rather than fetched and folded, because
        the table is append-only and a pair may hold several: what decides
        whether a window has lapsed is the most recent one, and every earlier row
        is history the falsifier reads separately.
        """

        if not candidate_ids:
            return {}
        rows = await self._session.execute(
            select(PassORM.passed_id, func.max(PassORM.passed_at))
            .where(
                PassORM.passer_id == passer_id,
                PassORM.sport == sport.value,
                PassORM.passed_id.in_(list(candidate_ids)),
            )
            .group_by(PassORM.passed_id)
        )
        return {passed_id: _utc(at) for passed_id, at in rows.all()}


def _utc(value: datetime) -> datetime:
    """A stored moment, read back as the UTC it was written as.

    The same seam the search store and the interest ledger have, for the same
    reason: PostgreSQL's ``timestamptz`` carries the offset and SQLite does not,
    and the value was written as UTC — so reading it as anything else would move
    it, which here would move a suppression window by hours.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value
