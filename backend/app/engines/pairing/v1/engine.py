"""Pairing v1 — the balance forecast, at its smallest complete size.

This version forecasts a **singles** match: tennis and squash, two seats, two
sides of one player each. The three doubles splits, the seat target, the target
band and seat imputation extend this version rather than replacing it, because a
shipped version is a directory that is never deleted — a forecast is interpretable
only through the code that produced it.

The whole calculation, in the order it happens:

1. **Two sides.** A team of one is that player, so singles reaches the arithmetic
   with no pairing step in front of it. Sides are oriented so that the current
   player, when they are on a seat, is the first one.
2. **The gap between them**, as a distribution rather than a number: its mean is
   the difference of the two strengths and its spread is the two Uncertainties
   combined in quadrature — into the gap, not across the roster.
3. **The expected absolute gap.** ``E|X|``, never ``|E X|``, so a wide Uncertainty
   inflates the gap instead of being reported as a confident near-zero.
4. **One clamp, on that gap.** The percentage floor and the favourite cap are both
   derived from it, so they saturate at the same instant and a card cannot print a
   floored number beside an unfloored bar.
5. **One rounding.** The percentage is rounded, and the split bar is derived from
   the rounded value, so the two cannot drift apart in the last decimal.
6. **A margin, and a grade of it.** The margin is the standard deviation of the
   same absolute gap, in the same percentage points as the estimate. There is no
   separate uncertainty penalty anywhere: uncertainty reaches the percentage only
   through the gap, which is what makes the percentage and the bar two views of
   one number with no correction term.
"""

from __future__ import annotations

from typing import final

from app.engines.forecast import (
    BalanceForecast,
    Certainty,
    PairingAnalysis,
    SidesNotFormed,
)
from app.engines.matchmaking import MatchSnapshot, PlayerSkill
from app.engines.pairing.core import (
    Side,
    absolute_gap_deviation,
    as_float,
    combine_uncertainty,
    expected_absolute_gap,
    round_half_away_from_zero,
    side_of_one,
)
from app.engines.pairing.v1.constants import CONSTANTS, ENGINE_VERSION
from app.kernel import Err, Instant, Ok, invariant

#: The seat count this version can form sides for. Read from the snapshot's own
#: sold count, which comes from the kernel registry, so a two-seat sport is
#: recognised by the registry and never by a list of sport names kept here.
_SIDES = 2


@final
class PairingEngineV1:
    """The v1 balance-forecast engine. Pure: no clock, no randomness, no state."""

    @property
    def version(self) -> str:
        return ENGINE_VERSION

    def analyse(self, *, snapshot: MatchSnapshot, now: Instant) -> PairingAnalysis:
        """Everything this engine concludes about one match, in one object.

        ``now`` is unread by the balance forecast — nothing about how even a match
        will be depends on when it is asked — and it is still an explicit input,
        because the analysis object grows terms that do depend on it and because a
        result reproducible from its stored inputs is the whole basis of the
        falsification programme. That it is **rounded to the minute** is a
        precondition and is checked as one: an engine handed a instant carrying
        seconds would produce a result no cache could ever hit and no replay could
        reproduce, which is a caller's bug and not a domain state.
        """

        invariant(
            now.second == 0 and now.microsecond == 0,
            f"now is not rounded to the minute: {now!r}",
        )

        sides = _sides_of(snapshot)
        if sides is None:
            return PairingAnalysis(
                forecast=Err(
                    SidesNotFormed(
                        sport=snapshot.sport.value,
                        seated=len(snapshot.occupants),
                        sold=snapshot.sold_seats,
                    )
                ),
                engine_version=ENGINE_VERSION,
            )

        first, second = sides
        return PairingAnalysis(
            forecast=Ok(_forecast(first, second)),
            engine_version=ENGINE_VERSION,
        )


def _sides_of(snapshot: MatchSnapshot) -> tuple[Side, Side] | None:
    """The two sides, or nothing when this version cannot form them.

    Two reasons it cannot, and they are one reason: there is nobody to put on a
    side. A four-seat sport needs the three splits, which is the next slice; a
    seat with no occupant needs imputation, which is the slice after it. Until
    then the engine declines rather than guessing, because a forecast built on a
    player who is not there is the failure this whole spec exists to remove.
    """

    if snapshot.sold_seats != _SIDES:
        return None
    occupants = snapshot.occupants
    if len(occupants) != _SIDES:
        return None
    first, second = _oriented(occupants, snapshot.current_player)
    return side_of_one(first), side_of_one(second)


def _oriented(
    occupants: tuple[PlayerSkill, ...], current: PlayerSkill
) -> tuple[PlayerSkill, PlayerSkill]:
    """Seat order, except that the current player comes first when they are in it.

    Every matchmaking answer is relative to somebody, and a card drawing *you
    against them* from a result whose sides are in seat order would draw it the
    wrong way round for half of all matches. Orientation is the engine's job
    because the engine is the only place that knows which side each strength
    belongs to.
    """

    first, second = occupants
    if second.player == current.player and first.player != current.player:
        return second, first
    return first, second


def _forecast(side_a: Side, side_b: Side) -> BalanceForecast:
    """The arithmetic, once both sides exist."""

    mean = as_float(side_a.strength) - as_float(side_b.strength)
    spread = combine_uncertainty(side_a.sigma, side_b.sigma)

    gap = expected_absolute_gap(mean, spread)
    deviation = absolute_gap_deviation(mean, spread)

    clamp = as_float(CONSTANTS.gap_clamp)
    coefficient = as_float(CONSTANTS.gap_coefficient)
    beyond_scale = gap > clamp

    # The clamp is what the *scale* does, and it is applied to exactly one
    # quantity. `expected_gap` below carries the unclamped expectation, because a
    # caller comparing two mismatches still needs to know that one of them is
    # worse — and because "the reported gap is never below the absolute expected
    # gap" is an invariant a clamped field would break at the top of the scale.
    estimate = round_half_away_from_zero(100.0 - coefficient * min(gap, clamp))

    # The margin is deliberately not clamped with it. It says how wrong the
    # estimate could be, and a mismatch the platform is unsure about is a
    # different claim from a mismatch it is sure of.
    margin = round_half_away_from_zero(coefficient * deviation)

    underdog_share = estimate // 2
    return BalanceForecast(
        estimate=estimate,
        margin=margin,
        certainty=_grade(margin),
        favourite_share=100 - underdog_share,
        underdog_share=underdog_share,
        beyond_scale=beyond_scale,
        side_a=side_a.strength,
        side_b=side_b.strength,
        expected_gap=gap,
    )


def _grade(margin: int) -> Certainty:
    """The margin, graded. The only thing that decides whether a card prints."""

    if margin <= CONSTANTS.certain_margin:
        return Certainty.HIGH
    if margin <= CONSTANTS.unsure_margin:
        return Certainty.MODERATE
    return Certainty.LOW
