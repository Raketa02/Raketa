"""``RatingHistories`` over the rating's own streams — **signed here**, so the
arrow runs ``rankings → rating`` and the rating knows nothing of the ranking.

**The rating's events are the record the ranking folds**: its opening
``rating.rating_initialised`` and every ``rating.moved_on_result``, read as the
rating context recorded them, never re-derived. A player's history is one
addressed stream — its id is the pair — and the rebuild walks every rating
stream in the order they were opened.

**It replays and remembers nothing**: no version is kept, so nothing read here
can be saved back onto a rating. Each event's **stored id** rides along, because
it is what keys that event's point in the level history (#769).

**The filing is the rating's own**: ``RATING_AGGREGATE`` and ``skill_rating_id``
are imported rather than respelled, so a rename there is a rename here — the
same stance the rating's published read takes, beside which this one sits.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import final
from uuid import UUID

from app.application.events import StoredDomainEvent
from app.application.ports import DomainEventStore
from app.kernel import Sport, instant
from app.modules.rankings.domain.ranking import LevelMove, RatingHistory
from app.modules.rating.domain.events import RatingInitialised, RatingMovedOnResult
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)


@final
class RatingStreamHistories:
    def __init__(self, *, event_store: DomainEventStore) -> None:
        self._event_store = event_store

    async def history_of(self, player_id: UUID, sport: Sport) -> RatingHistory | None:
        return await self._replayed(skill_rating_id(player_id, sport))

    async def every_history(self) -> Sequence[RatingHistory]:
        histories = []
        for rating_id in await self._event_store.find_aggregate_ids_by_first_event(
            aggregate_type=RATING_AGGREGATE, payload_equals={}
        ):
            history = await self._replayed(rating_id)
            if history is not None:
                histories.append(history)
        return tuple(histories)

    async def _replayed(self, rating_id: UUID) -> RatingHistory | None:
        stored = await self._event_store.load_stream(
            aggregate_type=RATING_AGGREGATE, aggregate_id=rating_id
        )
        return _history(stored)


def _history(records: Iterable[StoredDomainEvent]) -> RatingHistory | None:
    opening: RatingInitialised | None = None
    opened_by: UUID | None = None
    moves: list[LevelMove] = []
    for record in records:
        event = record.event
        if isinstance(event, RatingInitialised):
            opening, opened_by = event, record.id
        elif isinstance(event, RatingMovedOnResult):
            moves.append(
                LevelMove(
                    game_id=event.game_id,
                    won=event.won,
                    mu=event.mu,
                    sigma=event.sigma,
                    at=instant(event.occurred_at),
                    event_id=record.id,
                )
            )
    if opening is None or opened_by is None:
        return None
    return RatingHistory(
        player_id=opening.player_id,
        sport=Sport(opening.sport),
        initial_mu=opening.mu,
        initialised_at=instant(opening.occurred_at),
        moves=tuple(moves),
        opened_by=opened_by,
    )
