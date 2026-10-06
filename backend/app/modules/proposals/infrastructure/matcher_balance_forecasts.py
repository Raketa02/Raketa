"""``BalanceForecasts`` by **the engine's own forecast**, never a second one.

A card's percentage is the claim a booked game's screen prints too — *how even
will this be* — and both read it through one function,
``matchmaking/domain/balance.py``'s ``forecast_the_sides``: the engine's own
forecast over the two sides' Levels and Uncertainties, the released ruleset's
balance rules and the group σ as the matcher composes it. A side short of a seat
is read **as if the missing player matched the one there**, which is what the
engine's ``provisional`` means, and the card says so.

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
from app.kernel import Sport
from app.modules.matchmaking.domain.balance import forecast_the_sides
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
        read: list[CardForecast | None] = []
        for option in options:
            sides = forecast_the_sides(
                option.yours,
                option.theirs,
                levels,
                sport=sport,
                rules=self._ruleset.balance,
            )
            read.append(
                None
                if sides is None
                else CardForecast(pct=sides[0].pct, provisional=sides[0].provisional)
            )
        return read
