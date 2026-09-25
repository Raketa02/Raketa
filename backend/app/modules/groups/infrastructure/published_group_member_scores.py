"""``GroupMemberScores`` over ``player_score``'s published read. **No
arithmetic.**

``PlayerScore.published`` is the figure a player card, a record and the matcher
already read, so it is copied across the seam rather than blended again — a
second blend here would be a second place for the number a person reads about
themselves to be true.

**Absence passes straight through**: a player the platform has watched nothing
of is missing from the provider's answer and from this one, and a Members row
prints no score for them rather than a nought.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.player_score.domain.ports import PublishedScoreQuery


@final
class PublishedGroupMemberScores:
    def __init__(self, scores: PublishedScoreQuery) -> None:
        self._scores = scores

    async def scores_of(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, int]:
        wanted = set(player_ids)
        if not wanted:
            return {}
        published = await self._scores.scores_for(wanted, now=now)
        return {player_id: score.published for player_id, score in published.items()}
