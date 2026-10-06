"""How even a game between two sides is forecast to be — **one reading, two readers.**

A Games card prints *how even will this be* for the people on it
(``proposals``' ``MatcherBalanceForecasts``), and a booked game's screen prints
the same figure for the same people with the two side strengths beside it
(``GamesCourtPairing``, #575). They have to come to one number for one court, so
they read it here, once: the engine's ``forecast_and_split`` over the two sides'
Levels and Uncertainties, the released ruleset's balance rules, the group σ as
the matcher composes it, and the sport's own seat count.

**A side short of a seat is read as if the missing player matched the one there**
— the engine's ``provisional`` — which is honest on a card still filling. A side
with nobody on it, a side over the sport's seat count, or anybody on either side
with no Level in the sport leaves nothing to read: the answer is ``None`` rather
than a number guessed at, the rule every read here applies to a fact nobody
measured. **Pure**: the Levels are handed in, read live off ``rating`` by the
caller.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

from app.engines.matchfit.grouping import Forecast, Split
from app.engines.matchfit.ruleset import BalanceRules
from app.engines.matchfit.scorable import LevelReading
from app.engines.matchfit.v1 import forecast_and_split
from app.engines.racketskill.core import SkillEstimate
from app.kernel import Sport
from app.modules.matchmaking.domain.fence import combine_group_sigma
from app.modules.matchmaking.domain.lineups import seats_per_side


def forecast_the_sides(
    yours: Sequence[UUID],
    theirs: Sequence[UUID],
    levels: Mapping[UUID, SkillEstimate],
    *,
    sport: Sport,
    rules: BalanceRules,
) -> tuple[Forecast, Split] | None:
    """The forecast and the two strengths it was read from, ``yours`` first.

    ``None`` where a side is empty, over the sport's seat count, or holds
    somebody with no Level in ``levels``.
    """

    per_side = seats_per_side(sport)
    if any(
        not side
        or len(side) > per_side
        or any(player not in levels for player in side)
        for side in (yours, theirs)
    ):
        return None
    return forecast_and_split(
        _readings(yours, levels),
        _readings(theirs, levels),
        rules,
        combine_group_sigma,
        seats_per_side=per_side,
    )


def _readings(
    side: Sequence[UUID], levels: Mapping[UUID, SkillEstimate]
) -> tuple[LevelReading, ...]:
    return tuple(
        LevelReading(mu=levels[player].mu, sigma=levels[player].sigma)
        for player in side
    )


__all__ = ["forecast_the_sides"]
