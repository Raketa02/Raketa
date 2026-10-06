"""A court's people read together — how even two sides are, and the hours
everybody shares.

**What the new games kept of the group objective** (#580, PRD #569). The
objective that seated four people for a search — ``G``, its six terms, the cross
readings, the three arrangements and their reason codes — went with the ranking;
nothing the new games call seats anybody by it. Two readings survived because
the new games read them:

``forecast`` / ``forecast_and_split``
    How even a game between two sides is forecast to be. The proposer ranks a
    court's possible sides by it, a Games card prints it
    (``proposals``' ``MatcherBalanceForecasts``) and a booked game's screen
    prints it with the two side strengths (``GamesCourtPairing``, #575) — all
    through ``matchmaking/domain/balance.py``.

``group_availability``
    The share of the narrowest week everybody on a card shares, which a Games
    card's overlap grade cuts three ways (``proposals/domain/overlap.py``).

**No constants live here.** Every number comes off the ruleset's balance rules,
because changing one must be a dated release rather than a code change
(``docs/adr/0093``).
"""

from __future__ import annotations

from typing import Sequence

from app.engines.matchfit.core import ForecastAssumption
from app.engines.matchfit.grouping import Forecast, SigmaCombiner, Split
from app.engines.matchfit.ruleset import BalanceRules
from app.engines.matchfit.scorable import GridCell, LevelReading
from app.kernel import invariant


def forecast(
    side_a: tuple[LevelReading, ...],
    side_b: tuple[LevelReading, ...],
    rules: BalanceRules,
    combine: SigmaCombiner,
    *,
    seats_per_side: int = 2,
) -> Forecast:
    """How even the game is forecast to be, for two sides of one or two people.

    **One implementation produces the full figure and the provisional one**,
    which is what turns *the provisional figure becomes exactly the final figure
    the moment the seat fills* from a hope about two functions into a property of
    one (``docs/adr/0108``). A side with an empty seat is read **as if the
    missing player matched the one already there** — the sentence implemented
    literally, by seating that player twice — so the figure a half-empty side
    produced is exactly the figure the full side produces when the arrival
    matches, and the caveat lifts without the number moving.

    ``seats_per_side`` is **how many a full side holds in this sport**, and it is
    what decides whether a side of one is provisional or finished. A singles
    court is full at one a side, and marking that forecast provisional would
    caveat a number nothing was assumed about — the one lie a caveat can tell.
    It is a seat count and never a mode: ``kernel/sports.py`` fixes it per sport,
    and nothing here may guess it from how many people happened to be seated.

    ``pct`` is the printed whole percent and the σ is combined outside this
    engine. A forecast about four people is the same claim as a forecast about
    two, made over two side strengths instead of two players.
    """

    read, _ = forecast_and_split(
        side_a, side_b, rules, combine, seats_per_side=seats_per_side
    )
    return read


def forecast_and_split(
    side_a: tuple[LevelReading, ...],
    side_b: tuple[LevelReading, ...],
    rules: BalanceRules,
    combine: SigmaCombiner,
    *,
    seats_per_side: int = 2,
) -> tuple[Forecast, Split]:
    """:func:`forecast`, **and the two side strengths it was read from.**

    For a caller that prints both: a booked game's court is already seated, so
    the game screen reads it side against side from the people's Levels (#575),
    and the split it prints beside the percent has to be the pair the percent
    was computed from — so the two come out of one call to ``_predicted`` rather
    than two.

    ``side_a`` is the reader's side, which fixes the split's orientation.
    """

    pct, sigma, split = _predicted(side_a, side_b, rules, combine, seats_per_side)
    return (
        _forecast(
            pct,
            sigma,
            partial=len(side_a) < seats_per_side or len(side_b) < seats_per_side,
        ),
        split,
    )


def _forecast(pct: float, sigma: float, *, partial: bool) -> Forecast:
    """The forecast shape, built in one place so the caveat has one author."""

    return Forecast(
        pct=int(round(pct)),
        sigma_group=sigma,
        assumption=(
            ForecastAssumption.EMPTY_SEAT_MATCHES_ITS_PARTNER if partial else None
        ),
    )


def forecast_pct(gap: float, sigma: float, rules: BalanceRules) -> float:
    """``clamp(100 − gap·mu_coefficient − σ·sigma_coefficient, min, max)``.

    **One forecast, two sets of people.** A singles gap is between two players
    and a four's is between two side strengths, but the claim being made — *how
    even will this be* — is the same claim and reads the same three numbers.

    Unrounded: the card prints a whole percent of it, and :func:`_forecast` is
    the one place that rounds.
    """

    return min(
        float(rules.pct_max),
        max(
            float(rules.pct_min),
            100.0 - gap * rules.mu_coefficient - sigma * rules.sigma_coefficient,
        ),
    )


def group_availability(grids: Sequence[tuple[GridCell, ...]]) -> float | None:
    """``|shared| / min over everybody of |their declared slots|``. **No constants.**

    Good pairwise overlaps do not imply a shared one: one person free Monday and
    Tuesday, one free Monday, one free Tuesday and one free Monday overlap in
    pairs and give **a four with no common hour**. This reads the whole court at
    once, which is what a Games card's overlap grade needs.

    The denominator is the **smallest** declared grid, because among four people
    there is no *mine* to measure against — so the group's coverage is measured
    against the person with least to give.

    **A reading and not a gate.** An empty intersection reads zero and the card
    grades it *Slim*; nothing is removed for it.

    **A blank grid is ``None``**: it is the only thing between this reading and a
    division by zero, and *blank means we do not know* is a different claim from
    *you four never overlap*.
    """

    if any(not grid for grid in grids):
        return None
    shared = frozenset(grids[0]).intersection(*(frozenset(g) for g in grids[1:]))
    return len(shared) / min(len(grid) for grid in grids)


def _predicted(
    side_a: tuple[LevelReading, ...],
    side_b: tuple[LevelReading, ...],
    rules: BalanceRules,
    combine: SigmaCombiner,
    seats_per_side: int = 2,
) -> tuple[float, float, Split]:
    """The unrounded forecast, the group σ behind it, and the split it read.

    **The split comes back beside them rather than being re-derived by whoever
    wants it**, because the screen prints exactly the two strengths the forecast
    was computed from: one computation, and no second subtraction anywhere for
    them to disagree in.

    ``side_a`` is the reader's own side, and that is what fixes the split's
    orientation.
    """

    a = _seated_to_fill(side_a, seats_per_side)
    b = _seated_to_fill(side_b, seats_per_side)
    sigma = combine([level.sigma for level in a + b])
    split = Split(your_side=_strength(a, rules), their_side=_strength(b, rules))
    return forecast_pct(split.side_gap, sigma, rules), sigma, split


def _seated_to_fill(
    side: tuple[LevelReading, ...], seats_per_side: int
) -> tuple[LevelReading, ...]:
    """A full side, seating a lone player twice — *the* provisional assumption.

    Stated once, here, so that everything downstream of it — the strength, the
    σ, the printed percent — reads a full side and no caller has a second chance
    to interpret an empty seat.

    A singles side is full at one, so nothing is assumed and nothing is doubled:
    the same function answers both sports because *fill the side* is the same
    sentence, and the seat count is the only thing that differs.
    """

    invariant(
        1 <= len(side) <= seats_per_side,
        f"a side of {len(side)} where {seats_per_side} sit: an empty side is "
        f"not a side, and a side over its seat count is not one either",
    )
    return side if len(side) == seats_per_side else side * seats_per_side


def _strength(side: tuple[LevelReading, ...], rules: BalanceRules) -> float:
    """A side's strength. **The weaker partner sets more of it.**

    A doubles pair is attacked at its weaker half all evening, so the two shares
    are not a half each — ``the-group-objective.md`` §3.1's
    ``TEAM_STRENGTH_SHARE`` — and it is precisely that inequality which makes the
    three ways of splitting one four three different games, which is what the
    proposer chooses between.
    """

    stronger = max(level.mu for level in side)
    weaker = min(level.mu for level in side)
    share = rules.stronger_partner_share
    return share * stronger + (1.0 - share) * weaker


__all__ = [
    "forecast",
    "forecast_and_split",
    "forecast_pct",
    "group_availability",
]
