"""``RatedGroupMembers`` over the rating context's published read.

**One batch per sport, over the union of every member the answer is about** —
a list of groups asks once, never once per group. ``RatedPlayerQuery`` replays a
stream per ``(player, sport)``, which is the cost ``docs/adr/0183`` names beside
its dots (*a Groups list costs a ratings read*), free at seed scale and the first
thing to cache when a list slows down.

It reads the rating context's port and never its repository, which remembers
stream versions so a rating it found can be moved: a dot has no business holding
that.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from app.kernel import Sport
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
