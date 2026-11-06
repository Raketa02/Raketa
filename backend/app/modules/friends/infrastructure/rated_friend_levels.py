"""``FriendLevels`` over rating's **published** read: the Level and the band's
name as the rating committed them, derived from nothing here."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from app.kernel import Sport
from app.modules.friends.domain.ports import FriendLevel
from app.modules.rating.domain.ports import RatedPlayerQuery


class RatedFriendLevels:
    def __init__(self, ratings: RatedPlayerQuery) -> None:
        self._ratings = ratings

    async def levels_in(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, FriendLevel]:
        wanted = set(player_ids)
        if not wanted:
            return {}
        published = await self._ratings.published_for(wanted, sport=sport)
        return {
            player_id: FriendLevel(sport=sport, level=rating.mu, band=rating.band_name)
            for player_id, rating in published.items()
        }
