"""``RatedPlayerQuery`` over the rating streams.

**Addressed, never searched.** A rating's stream id is derived from
``(player, sport)``, so reading a batch is one ``load_stream`` per pair rather
than a query with a predicate — and a player who has never been rated in that
sport is a stream that does not exist, which is the same answer as *absent from
the reply* with nothing to translate.

**It replays and remembers nothing.** No version is recorded, so an aggregate
that came out of here cannot be saved through the repository beside it: the
narrowness is the point of the port, and this is where it is real rather than
promised.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.application.ports import DomainEventStore
from app.engines.racketskill.core import SkillEstimate
from app.kernel import Sport
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    RATING_AGGREGATE,
)


@final
class EventSourcedRatedPlayers:
    """``RatedPlayerQuery`` over ``DomainEventStore``."""

    def __init__(self, *, event_store: DomainEventStore) -> None:
        self._event_store = event_store

    async def estimates_for(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, SkillEstimate]:
        found: dict[UUID, SkillEstimate] = {}
        # Sorted, so a batch is replayed in the same order on every process. The
        # answer is a mapping and could not care, but the *reads* are what a
        # future trace or a lock ordering would care about, and a sorted walk
        # costs nothing to keep (``docs/adr/0105``).
        for player_id in sorted(set(player_ids)):
            stored = await self._event_store.load_stream(
                aggregate_type=RATING_AGGREGATE,
                aggregate_id=skill_rating_id(player_id, sport),
            )
            if not stored:
                continue
            rating = SkillRating.from_history(record.event for record in stored)
            found[player_id] = rating.estimate
        return found


__all__ = ["EventSourcedRatedPlayers"]
