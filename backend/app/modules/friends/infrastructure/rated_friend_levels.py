"""``FriendLevels`` over rating's **published** reads: the Level and the band's
name as the rating committed them, derived from nothing here — one sport for a
batch (``published_for``), or every sport for a batch (``ratings_of_each``)."""

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

    async def levels_of(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, tuple[FriendLevel, ...]]:
        """Every sport, through rating's batch of the record's read — one
        statement for the row, and the same published figures as
        ``levels_in``."""

        wanted = set(player_ids)
        if not wanted:
            return {}
        held = await self._ratings.ratings_of_each(wanted)
        return {
            player_id: tuple(
                FriendLevel(sport=sport, level=rating.mu, band=rating.band_name)
                for sport in Sport
                if (rating := sports.get(sport)) is not None
            )
            for player_id, sports in held.items()
            if sports
        }
