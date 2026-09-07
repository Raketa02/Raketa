"""``LapsingChallengeQuery`` over the event log — **the sweep's candidate set.**

**It reads no payload and folds nothing.** The other two reads this context has
over the log match on the serialized seats and then replay what they find; this
one answers with ids alone, because the loop behind it is going to load every
one of them through the aggregate repository anyway and a second replay here
would be the same stream read twice.

**The whole narrowing is one column comparison, and it is exact rather than
heuristic.** A seat's ``answer_by`` is the seating event that created it plus
``ANSWER_WINDOW`` — ``answer_window.py`` is the only place that arithmetic
happens — so a challenge holds a seat whose window has passed at ``now`` only if
one of its events occurred at or before ``now`` minus that window. A stream's
earliest event is its opening, so *any* row inside the cutoff names a challenge
old enough to have one, and every challenge younger than the cutoff is excluded
with certainty.

**What it does not narrow on is the seat itself**, and that is the decision
rather than a limitation. Whether a particular seat is still awaiting lives in a
seat code inside a JSON array; a column that answered it would be the derived
standing, stored — which is the thing ``standing.py`` refuses, and it would be
wrong for exactly the gap this loop exists to close. So this over-names: a
challenge everybody answered, one already swept and a mutual-born one with no
deadline anywhere on it are all candidates once they are a day old, and each
costs a stream read and an aggregate that appends nothing.

**Cost.** Grows with challenges ever recorded rather than with the backlog, and
``occurred_at`` carries no index — the same position ``challenge_streams.py``
takes about its substring match, for the same reason: the index that fixes it is
PostgreSQL's, over a table with no rows on a platform with no deployed
environment, and it belongs with the first query that measures it. What is
written down here instead is the shape the fix takes — the loop is the one caller
that could be given a cursor, because a seat lapses exactly one window after an
event the log already orders.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Instant
from app.modules.challenges.domain.answer_window import ANSWER_WINDOW
from app.modules.challenges.infrastructure.event_sourced_challenge_repository import (
    CHALLENGE_AGGREGATE,
)


@final
class EventSourcedLapsingChallengeQuery:
    """The challenges a sweep at ``now`` has any reason to open."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def may_have_lapsed(self, *, now: Instant) -> tuple[UUID, ...]:
        """Every challenge stream that opened at or before one window ago.

        Ordered by the position its first event took in the log, which is
        oldest-first and is a **total** order — ``sequence_no`` is the only
        column here that is one (``event_store_model.py``), and ordering on
        ``occurred_at`` would leave two challenges opened in one commit to come
        back in whatever order the rows happened to arrive.
        """

        found = await self._session.execute(
            select(
                EventStoreORM.aggregate_id,
                func.min(EventStoreORM.sequence_no).label("opened"),
            )
            .where(
                EventStoreORM.aggregate_type == CHALLENGE_AGGREGATE,
                EventStoreORM.occurred_at <= now - ANSWER_WINDOW,
            )
            .group_by(EventStoreORM.aggregate_id)
            .order_by("opened")
        )
        return tuple(row.aggregate_id for row in found.all())
