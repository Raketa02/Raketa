"""``ScoredGames`` over the event log (#613).

**A third adapter rather than a method on either of the other two**, and the
line is again which read it starts from. ``EventSourcedGameHistory`` starts from
a player and folds whole streams; ``EventSourcedConfirmedResults`` starts from
nobody and folds every stream. This one starts from **game ids the caller
already holds** and folds nothing: one statement over the stream index — the
streams named, the three kinds of score, the moment — answering ids.

**It matches on three stored event names**, taken from this context's own
contract list (``contract_name``), so a renamed contract renames the match
rather than silently finding nothing.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Final, final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Instant
from app.modules.games.application.event_subscriptions import contract_name
from app.modules.games.domain.events import (
    ResultCorrected,
    ResultCountered,
    ResultProposed,
)
from app.modules.games.infrastructure.event_sourced_game_repository import (
    GAME_AGGREGATE,
)

#: Every event that puts a score on the table — and so starts, or restarts,
#: the other side's day to answer it.
_SCORES: Final = tuple(
    contract_name(event) for event in (ResultProposed, ResultCorrected, ResultCountered)
)


@final
class EventSourcedScoredGames:
    """``ScoredGames`` over ``event_store``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def scored_since(
        self, game_ids: Collection[UUID], *, since: Instant
    ) -> frozenset[UUID]:
        wanted = sorted(set(game_ids))
        if not wanted:
            return frozenset()
        found = await self._session.scalars(
            select(EventStoreORM.aggregate_id)
            .where(
                EventStoreORM.aggregate_type == GAME_AGGREGATE,
                EventStoreORM.aggregate_id.in_(wanted),
                EventStoreORM.event_type.in_(_SCORES),
                EventStoreORM.occurred_at >= since,
            )
            .distinct()
        )
        return frozenset(found.all())
