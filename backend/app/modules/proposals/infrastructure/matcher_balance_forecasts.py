"""``BalanceForecasts`` by **the engine's own forecast**, never a second one.

A card's percentage is the claim a line-up, a challenge card and a game screen
already print — *how even will this be* — and it is made by one function,
``engines/matchfit/v1``'s ``forecast``, over the two sides' Levels and
Uncertainties, the released ruleset's balance rules and the group σ as the
matcher composes it (``combine_group_sigma``). A side short of a seat is read
**as if the missing player matched the one there**, which is what the engine's
``provisional`` means, and the card says so.

**Levels off rating's estimates, live** — the engine's currency, the one
``PlayerFit`` gates on beside it — and never the candidate index, so a card
needs no index to draw its forecast. Somebody not rated in the sport leaves the
forecast absent rather than guessed, the rule every read here applies to a fact
nobody measured.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import final

from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scorable import LevelReading
from app.engines.matchfit.v1 import forecast
from app.kernel import Sport
from app.modules.matchmaking.domain.fence import combine_group_sigma
from app.modules.matchmaking.domain.lineups import seats_per_side
from app.modules.proposals.domain.deck import CardForecast, Sides
from app.modules.rating.domain.ports import RatedPlayerQuery


@final
class MatcherBalanceForecasts:
    def __init__(self, *, ratings: RatedPlayerQuery, ruleset: Ruleset) -> None:
        self._ratings = ratings
        self._ruleset = ruleset

    async def forecasts(
        self, options: Sequence[Sides], *, sport: Sport
    ) -> Sequence[CardForecast | None]:
        people = {
            player for option in options for player in (*option.yours, *option.theirs)
        }
        if not people:
            return [None for _ in options]
        levels = await self._ratings.estimates_for(people, sport=sport)
        per_side = seats_per_side(sport)
        read: list[CardForecast | None] = []
        for option in options:
            sides = (option.yours, option.theirs)
            if any(
                not side
                or len(side) > per_side
                or any(player not in levels for player in side)
                for side in sides
            ):
                read.append(None)
                continue
            yours, theirs = (
                tuple(
                    LevelReading(mu=levels[player].mu, sigma=levels[player].sigma)
                    for player in side
                )
                for side in sides
            )
            forecast_of = forecast(
                yours,
                theirs,
                self._ruleset.balance,
                combine_group_sigma,
                seats_per_side=per_side,
            )
            read.append(
                CardForecast(pct=forecast_of.pct, provisional=forecast_of.provisional)
            )
        return read
