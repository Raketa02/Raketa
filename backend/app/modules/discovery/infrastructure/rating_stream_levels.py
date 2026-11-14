"""``LevelSources`` over the rating's own streams — **signed here**, so the
arrow runs ``discovery → rating`` and the rating knows nothing of the rows
(#794; ``docs/adr/0204`` §10).

**Where a stream stands is its last event**: the opening
``rating.rating_initialised`` — the questionnaire's Level — or the latest
``rating.moved_on_result``, each carrying the Level, its Uncertainty and the
band as the rating published them, never re-derived. How many results stand on
it rides along, which is what keeps the projection's fold the newest.

**The filing is the rating's own**: ``RATING_AGGREGATE`` and
``skill_rating_id`` are imported rather than respelled, as the ranking's
``RatingStreamHistories`` does beside it. It replays and remembers nothing: no
version is kept, so nothing read here can be saved back onto a rating.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import final
from uuid import UUID

from app.application.events import StoredDomainEvent
from app.application.ports import DomainEventStore
from app.kernel import Sport
from app.modules.discovery.domain.levels import Band, CurrentLevel
from app.modules.rating.domain.events import RatingInitialised, RatingMovedOnResult
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)


@final
class RatingStreamLevels:
    def __init__(self, *, event_store: DomainEventStore) -> None:
        self._event_store = event_store

    async def level_of(self, player_id: UUID, sport: Sport) -> CurrentLevel | None:
        return await self._stands_at(skill_rating_id(player_id, sport))

    async def every_level(self) -> Sequence[CurrentLevel]:
        levels = []
        for rating_id in await self._event_store.find_aggregate_ids_by_first_event(
            aggregate_type=RATING_AGGREGATE, payload_equals={}
        ):
            level = await self._stands_at(rating_id)
            if level is not None:
                levels.append(level)
        return tuple(levels)

    async def _stands_at(self, rating_id: UUID) -> CurrentLevel | None:
        return _standing(
            await self._event_store.load_stream(
                aggregate_type=RATING_AGGREGATE, aggregate_id=rating_id
            )
        )


def _standing(records: Iterable[StoredDomainEvent]) -> CurrentLevel | None:
    last: RatingInitialised | RatingMovedOnResult | None = None
    results = 0
    for record in records:
        event = record.event
        if isinstance(event, RatingInitialised):
            last = event
        elif isinstance(event, RatingMovedOnResult):
            last = event
            results += 1
    if last is None:
        return None
    return CurrentLevel(
        player_id=last.player_id,
        sport=Sport(last.sport),
        mu=last.mu,
        sigma=last.sigma,
        band=Band(name=last.band_name, lower=last.band_lower, upper=last.band_upper),
        results=results,
    )
