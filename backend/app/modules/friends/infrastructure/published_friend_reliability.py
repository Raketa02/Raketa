"""``FriendReliabilities`` over ``player_score``'s published figure — the points
and the band a Members row prints, copied and never re-derived."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from app.kernel import Instant
from app.modules.friends.domain.ports import FriendReliability
from app.modules.player_score.domain.ports import PublishedScoreQuery


class PublishedFriendReliability:
    def __init__(self, scores: PublishedScoreQuery) -> None:
        self._scores = scores

    async def reliability_of(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, FriendReliability]:
        wanted = set(player_ids)
        if not wanted:
            return {}
        published = await self._scores.scores_for(wanted, now=now)
        return {
            player_id: FriendReliability(points=score.points, band=score.band)
            for player_id, score in published.items()
        }
