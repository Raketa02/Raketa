"""``SportLevels`` over rating's **published** read — a rating in the sport,
read live, never the projection's copy."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Sport
from app.modules.rating.domain.ports import RatedPlayerQuery


@final
class RatedSportLevels:
    def __init__(self, ratings: RatedPlayerQuery) -> None:
        self._ratings = ratings

    async def holds_a_level(self, player_id: UUID, sport: Sport) -> bool:
        return player_id in await self._ratings.estimates_for([player_id], sport=sport)
