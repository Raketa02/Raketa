"""``PlayersInPlay`` — a Level from rating, a week from the Player profile.

**The engine's currency**: rating's estimates, Level and Uncertainty, the ones
``PlayerFit`` gates on and the forecasts read — never the candidate index, so
the proposer needs no index to deal. One set read of the estimates and one
profile stream per member, sorted so every process reads in one order
(``docs/adr/0105``).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.engines.matchfit.scorable import LevelReading
from app.kernel import Sport
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.ports import InPlay
from app.modules.rating.domain.ports import RatedPlayerQuery


@final
class ProfilePlayersInPlay:
    def __init__(
        self, *, profiles: PlayerProfileRepository, ratings: RatedPlayerQuery
    ) -> None:
        self._profiles = profiles
        self._ratings = ratings

    async def of(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, InPlay]:
        wanted = sorted(set(player_ids))
        if not wanted:
            return {}
        estimates = await self._ratings.estimates_for(wanted, sport=sport)
        answer: dict[UUID, InPlay] = {}
        for player_id in wanted:
            profile = await self._profiles.load(player_id)
            estimate = estimates.get(player_id)
            answer[player_id] = InPlay(
                level=None
                if estimate is None
                else LevelReading(mu=estimate.mu, sigma=estimate.sigma),
                week=profile.weekly_hours
                if profile is not None
                else WeeklyHours.blank(),
            )
        return answer
