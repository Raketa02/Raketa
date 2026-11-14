"""``LevelsHeld`` over rating's **published** read: each person's Level in
every sport they hold one in, as the rating committed it — derived from
nothing here. One batch per sport, in the sports' own order (``Sport`` itself,
so a fifth sport is read without anybody widening a list)."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.kernel import Sport
from app.modules.discovery.domain.ports import SportLevel
from app.modules.rating.domain.ports import RatedPlayerQuery


@final
class PublishedLevelsHeld:
    def __init__(self, ratings: RatedPlayerQuery) -> None:
        self._ratings = ratings

    async def levels_of(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, tuple[SportLevel, ...]]:
        wanted = set(player_ids)
        held: dict[UUID, list[SportLevel]] = {player_id: [] for player_id in wanted}
        if not wanted:
            return {}
        for sport in Sport:
            for player_id, rating in (
                await self._ratings.published_for(wanted, sport=sport)
            ).items():
                held[player_id].append(SportLevel(sport=sport, level=rating.mu))
        return {player_id: tuple(levels) for player_id, levels in held.items()}
