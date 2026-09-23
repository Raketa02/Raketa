"""``LeftCourtQuery`` over the event log — **the hour's candidate set**
(``docs/adr/0175`` §3).

**It reads no payload and folds nothing**, on
``event_sourced_lapsing_challenge_query.py``'s argument: the sweep loads every
challenge it is named through the aggregate repository and asks the fold, so
answering with ids alone is the one read rather than the same stream read twice.

**The whole narrowing is one event type.** A court that has been a game is
short of a player only because somebody left it — ``challenges.seat_left`` is
the one event that reopens a seat on such a court — so a stream with none has
nothing for the sweep and is excluded with certainty, and one with any is named
whether or not it is still short, still a game, or was ever one. A departure
before the court was whole names a candidate the fold answers *never a game*
for; a court since re-seated, one already called off, and one whose hour is
still ahead each cost a stream read and nothing written. **Over-naming is free
and under-naming is not.**

**Cost.** Grows with courts ever left rather than with the backlog, on the same
unindexed ``event_type`` the lapse read's ``occurred_at`` is, and with the same
position: the index is PostgreSQL's, over a table with no rows on a platform
with no deployed environment, and belongs with the first query that measures
it.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.challenges.infrastructure.event_sourced_challenge_repository import (
    CHALLENGE_AGGREGATE,
)

#: The durable name of ``SeatLeft`` — ``event_subscriptions.py``'s contract,
#: spelled here because this read matches on the column and never on the class.
SEAT_LEFT = "challenges.seat_left"


@final
class EventSourcedLeftCourtQuery:
    """The challenges the hour's sweep has any reason to open."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def courts_somebody_left(self) -> tuple[UUID, ...]:
        """Every challenge stream holding a departure, oldest first by the
        position its first departure took in the log — ``sequence_no``, the
        one total order the store has."""

        found = await self._session.execute(
            select(
                EventStoreORM.aggregate_id,
                func.min(EventStoreORM.sequence_no).label("left"),
            )
            .where(
                EventStoreORM.aggregate_type == CHALLENGE_AGGREGATE,
                EventStoreORM.event_type == SEAT_LEFT,
            )
            .group_by(EventStoreORM.aggregate_id)
            .order_by("left")
        )
        return tuple(row.aggregate_id for row in found.all())


__all__ = ["EventSourcedLeftCourtQuery", "SEAT_LEFT"]
