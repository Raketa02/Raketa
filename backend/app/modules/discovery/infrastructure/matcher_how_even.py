"""``HowEven`` by **the matcher's own forecast**, never a second one (#794;
``docs/adr/0204`` §4).

*Same competitive level*'s % even is the claim a Games card prints — *how even
would this be* — so it is read through the one function both the card and a
booked game's screen read, ``matchmaking/domain/balance.py``'s
``forecast_the_sides``: the engine's forecast over the released ruleset's
balance rules and the group σ as the matcher composes it, **one player a
side**. In a doubles sport the lone player on each side is seated twice — the
engine's *the empty seat matches its partner* — so the two are opposite sides
(call 8 of #790) and the figure is the singles one: the same gap and the same
pair σ. Its bounds (35–96) are the ruleset's.

The two are filed under fixed keys, since the forecast reads people by id and
these are readings, not people.
"""

from __future__ import annotations

from typing import Final, final
from uuid import UUID

from app.engines.matchfit.ruleset import Ruleset
from app.engines.racketskill.core import SkillEstimate
from app.kernel import Sport, invariant
from app.modules.discovery.domain.levels import Estimate
from app.modules.matchmaking.domain.balance import forecast_the_sides

_YOU: Final = UUID(int=1)
_THEM: Final = UUID(int=2)


@final
class MatcherHowEven:
    def __init__(self, ruleset: Ruleset) -> None:
        self._rules = ruleset.balance

    def percent_even(self, sport: Sport, yours: Estimate, theirs: Estimate) -> int:
        sides = forecast_the_sides(
            (_YOU,),
            (_THEM,),
            {
                _YOU: SkillEstimate(mu=yours.mu, sigma=yours.sigma),
                _THEM: SkillEstimate(mu=theirs.mu, sigma=theirs.sigma),
            },
            sport=sport,
            rules=self._rules,
        )
        forecast, _ = invariant(sides, "two players, each with a level, a side each")
        return forecast.pct
