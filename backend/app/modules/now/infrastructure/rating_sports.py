"""``RatedSports`` over the rating context's own repository.

The one place in Now that knows a rated sport is a ``SkillRating`` with a stream
behind it. It takes the *port*, not the adapter, so the composition root decides
which store answers and this file never learns that the rating context is
event-sourced.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Sport

from app.modules.now.domain.ports import RatedSports
from app.modules.rating.domain.ports import SkillRatingRepository


class RatedSportsFromSkillRatings(RatedSports):
    """Every sport this player holds a rating at, as a set."""

    def __init__(self, ratings: SkillRatingRepository) -> None:
        self._ratings = ratings

    async def for_player(self, player_id: UUID) -> frozenset[Sport]:
        held = await self._ratings.find_all_for(player_id=player_id)
        return frozenset(rating.sport for rating in held)

    async def holds(self, *, player_id: UUID, sport: Sport) -> bool:
        """One lookup, through the by-pair question the rating context already has.

        ``exists_for`` rather than ``sport in await self.for_player(...)``: the
        stream is keyed by the pair, so the question is one read where the set is
        a replay of every rating she holds. Its own docstring names this as the
        reason it is a question and not an aggregate.
        """

        return await self._ratings.exists_for(player_id=player_id, sport=sport)
