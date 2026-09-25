"""``RatedGroupMembers`` over the rating context's published read.

**One batch per sport, over the union of every member the answer is about** —
a list of groups asks once, never once per group. ``RatedPlayerQuery`` replays a
stream per ``(player, sport)``, which is the cost ``docs/adr/0183`` names beside
its dots (*a Groups list costs a ratings read*), free at seed scale and the first
thing to cache when a list slows down.

It reads the rating context's port and never its repository, which remembers
stream versions so a rating it found can be moved: a dot has no business holding
that. **A Level is the published one** (``published_for``) — the figure a rating
route already prints — and never the engine's estimate, so a Join request cannot
show its Owner a number the person's own record does not.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from app.kernel import Sport
from app.modules.groups.domain.ports import SportLevel
from app.modules.rating.domain.ports import RatedPlayerQuery


class RatingsRatedGroupMembers:
    def __init__(self, ratings: RatedPlayerQuery) -> None:
        self._ratings = ratings

    async def rated_in(
        self, player_ids: Collection[UUID]
    ) -> Mapping[Sport, frozenset[UUID]]:
        wanted = set(player_ids)
        if not wanted:
            return {}
        return {
            sport: frozenset(await self._ratings.estimates_for(wanted, sport=sport))
            for sport in Sport
        }

    async def levels_of(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, tuple[SportLevel, ...]]:
        wanted = set(player_ids)
        if not wanted:
            return {}
        levels: dict[UUID, list[SportLevel]] = {}
        for sport in Sport:
            published = await self._ratings.published_for(wanted, sport=sport)
            for player_id, rating in published.items():
                levels.setdefault(player_id, []).append(
                    SportLevel(sport=sport, level=rating.mu)
                )
        return {player_id: tuple(rows) for player_id, rows in levels.items()}
