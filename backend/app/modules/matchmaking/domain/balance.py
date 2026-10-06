"""How even a game between two sides is forecast to be — **one reading, two readers.**

A Games card prints *how even will this be* for the people on it
(``proposals``' ``MatcherBalanceForecasts``), and a booked game's screen prints
the same figure for the same people with the two side strengths beside it
(``GamesCourtPairing``, #575). They have to come to one number for one court, so
they read it here, once: the engine's ``forecast_and_split`` over the two sides'
Levels and Uncertainties, the released ruleset's balance rules, the group σ as
the matcher composes it, and the sport's own seat count.

**The two helpers the reading needs live here too** (#579): the group σ on the
two-player basis the forecast's coefficient is priced against, which the
proposer's own ranking of a court reads as well, and the sport's seat count.
They were the search's fence and its line-ups', and are what the new games kept.

**A side short of a seat is read as if the missing player matched the one there**
— the engine's ``provisional`` — which is honest on a card still filling. A side
with nobody on it, a side over the sport's seat count, or anybody on either side
with no Level in the sport leaves nothing to read: the answer is ``None`` rather
than a number guessed at, the rule every read here applies to a fact nobody
measured. **Pure**: the Levels are handed in, read live off ``rating`` by the
caller.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from functools import reduce
from uuid import UUID

from app.engines.matchfit.grouping import Forecast, Split
from app.engines.matchfit.ruleset import BalanceRules
from app.engines.matchfit.scorable import LevelReading
from app.engines.matchfit.v1 import forecast_and_split
from app.engines.racketskill.core import SkillEstimate, combine_sigma
from app.kernel import SPORT_SPECS, Sport, invariant


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


def combine_group_sigma(sigmas: Sequence[float]) -> float:
    """A group's spread, **on the two-player basis its coefficient is calibrated
    against** — ``√2 · rms(σ)``, which at two players *is* ``combine_sigma``.

    The forecast needs one Uncertainty over four Levels and may not derive
    it: ``combine_sigma`` is *the single place any engine is allowed to combine
    two standard deviations*, ``.importlinter`` forbids one engine to import the
    other, and ``√(Σσ²)`` written inside Match Fit would be a second definition of
    an identity that already has an owner. The quadrature fold is legitimate here
    because quadrature is associative: combining four is combining two, twice.

    ## The basis, which is the whole of what this function adds

    ``forecast_pct`` is **one function read by two populations** — a pairing of two
    and a four — and its ``sigma_coefficient`` is a released constant calibrated
    against *"a typical σ_pair of 0.495"* (``ranking-weights.md``, ``the-engine.md``,
    ADR-0103). A pairing's ``gap`` is between two players and a four's between two
    side strengths, and the four's gap **was** re-based for that. Its σ was not:
    ``√(Σσᵢ²)`` grows with ``√n``, so a four was handed a number ``√2`` larger than
    the pair the constant was priced for, and paid 1.41× for the identical
    per-player doubt. A level four of unsettled players read 46 % with a gap of
    exactly zero, and above σ 2.03 the clamp swallowed the gap entirely and the
    forecast stopped answering the question it is about.

    So the fold is normalised to the basis: ``√(2·Σσᵢ²/n)``. At ``n = 2`` it is
    ``√(σ₁²+σ₂²)`` exactly — the pair's own combination, unchanged, so singles and
    every pairwise reading are untouched by construction — and at ``n = 4`` it is
    the spread of a **representative pair drawn from the group**, which is the
    thing a match is actually played between.

    **This is a units correction, not a retune.** No released constant moves; the
    caller stops handing one a quantity on a scale it was never priced for. What is
    *not* settled by it is whether an outcome's uncertainty should discount the
    evenness figure at all, given ``sigma_group`` crosses beside it —
    ``docs/handovers/the-forecast-percentage.md`` holds that question.

    It is a **function** where a pair's combination is a value, because the
    engine fills an empty seat before it combines — nothing out here could have
    precomputed the spread of a side it has not seated.
    """

    invariant(bool(sigmas), "a spread over nobody at all")
    return reduce(combine_sigma, sigmas) * math.sqrt(2 / len(sigmas))


def seats_per_side(sport: Sport) -> int:
    """How many a **full side** holds. Two in doubles, one in singles.

    It is what decides whether a side of one is provisional or finished, and it
    is a seat count and never a mode: marking a singles forecast provisional
    would caveat a number nothing was assumed about.
    """

    return SPORT_SPECS[sport].players // 2


__all__ = ["combine_group_sigma", "forecast_the_sides", "seats_per_side"]
