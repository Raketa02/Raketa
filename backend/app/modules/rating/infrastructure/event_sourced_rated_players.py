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

**Both reads walk their subject in a declared order** — the batch over sorted
ids, the per-player read over ``Sport`` itself — and neither *answer* could tell,
because a mapping has no order. What is ordered is the **sequence of stream
loads**, which is what a trace, a lock ordering or a future retry would care
about, and a declared walk costs nothing to keep (``docs/adr/0105``).
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.application.ports import DomainEventStore
from app.engines.racketskill.core import SkillEstimate
from app.kernel import Sport
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.ports import RatedSport
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
            rating = await self._replayed(player_id, sport)
            if rating is not None:
                found[player_id] = rating.estimate
        return found

    async def ratings_of(self, player_id: UUID) -> Mapping[Sport, RatedSport]:
        """Every sport this player holds a rating in, replayed one stream each.

        **Four addressed loads and never a search.** A rating's stream id is
        derived from ``(player, sport)``, so *which sports is this person rated
        in* is answered by asking about each of them: a sport with no stream is a
        sport they hold no rating in, which is the same answer as *absent from
        the mapping* with nothing to translate.

        The walk is over ``Sport`` itself, so a fifth sport added to the registry
        is read here without anybody remembering to widen a list.
        """

        held: dict[Sport, RatedSport] = {}
        for sport in Sport:
            rating = await self._replayed(player_id, sport)
            if rating is None:
                continue
            held[sport] = RatedSport(
                sport=sport,
                mu=rating.mu,
                confidence=rating.confidence,
                range_low=rating.range_low,
                range_high=rating.range_high,
                band_name=rating.band_name,
                counted_results=rating.counted_results,
            )
        return held

    async def _replayed(self, player_id: UUID, sport: Sport) -> SkillRating | None:
        """One pair's rating, replayed, or ``None`` where the stream does not exist.

        The whole of *addressed, never searched*, written once: both reads above
        would otherwise each spell how a rating is found, and the first of the two
        to be changed would win for whichever consumer went through it.
        """

        stored = await self._event_store.load_stream(
            aggregate_type=RATING_AGGREGATE,
            aggregate_id=skill_rating_id(player_id, sport),
        )
        if not stored:
            return None
        return SkillRating.from_history(record.event for record in stored)


__all__ = ["EventSourcedRatedPlayers"]
