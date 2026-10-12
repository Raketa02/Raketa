"""``GroupMemberReliability`` over ``player_score``'s published read. **No
arithmetic.**

The points and the band are ``PlayerScore``'s — the figure and the word a
player's own record prints — so they are copied across the seam rather than
derived again: a second fold here would be a second place for the number a
person reads about themselves to be true.

**Everybody asked is answered**: everyone starts at a hundred (#659), so a
member nothing has happened to is a row reading 100, never a missing score.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.groups.domain.ports import MemberReliability
from app.modules.player_score.domain.ports import PublishedScoreQuery


@final
class PublishedGroupMemberReliability:
    def __init__(self, scores: PublishedScoreQuery) -> None:
        self._scores = scores

    async def reliability_of(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, MemberReliability]:
        wanted = set(player_ids)
        if not wanted:
            return {}
        published = await self._scores.scores_for(wanted, now=now)
        return {
            player_id: MemberReliability(points=score.points, band=score.band)
            for player_id, score in published.items()
        }
