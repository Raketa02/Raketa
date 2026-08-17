"""The pairing core — everything that must outlive a version.

A version directory owns the *constants*; this module owns the arithmetic those
constants feed, extracted now so that a later lineage cannot develop a second idea
of what the gap between two sides is.

**The reported gap is the expected absolute gap, never the absolute expected
gap**, and that one word is the whole treatment of uncertainty here. Two teams
whose strengths differ by nothing on paper do not play a dead-even match; they
play a match whose margin is unknown, and the wider the platform's Uncertainty
about them the larger that margin is *expected* to be, in whichever direction. So
the quantity reported is ``E|X|`` for ``X ~ N(mean, spread)``, the folded-normal
mean, which equals ``|mean|`` exactly when the platform is certain and grows above
it as it is not. Taking ``|E X|`` instead would report a confident near-zero for
four players nobody has ever watched, and — once three doubles splits are ranked
against each other — would pick whichever split noise had made look closest, an
optimism that grows with σ rather than shrinking.

That is also why there is no separate uncertainty penalty. Uncertainty reaches
the percentage through the one quantity the card is actually about, so the
percentage and the split bar are two views of one number with no correction term
between them.

**σ propagates into the gap, not across the roster.** Two independent estimates
are combined in quadrature, once, into the uncertainty of their *difference*.
Summing σ across four players measures the uncertainty of a different quantity
altogether and overstates doubles by roughly a factor of two — which is how the
source documents arrived at a perfectly balanced padel match reading 46% and every
forecast reading unsure, permanently.

**The rating engine is not imported.** ``racketskill/core`` owns a σ-combination
rule that is the same algebra, and it answers a different question: fusing several
pieces of evidence about *one* player. Reaching for it would put this engine's
version lineage at the mercy of a rating-engine retune, and the falsification
programme rests on being able to attribute a number to exactly one lineage. A
Level, an Uncertainty and a Confidence arrive here as values carried on the
snapshot, and the scale, the confidence transform and its ceiling are never
restated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import final

from app.engines.matchmaking import Level, PlayerSkill
from app.kernel import Ratio

#: ``√(2/π)``, the folded-normal mean's coefficient at a mean of zero. Named
#: because it is arithmetic rather than a hypothesis: retuning it would not
#: retune a product decision, it would make the expectation wrong.
_SQRT_TWO_OVER_PI = math.sqrt(2.0 / math.pi)


def as_float(value: Ratio) -> float:
    """The one place the exact vocabulary becomes floating point.

    A Level and an Uncertainty are exact ratios, and every quantity derived from
    Levels alone stays exact: a doubles team strength is a ``Ratio``-weighted
    blend, the gap between two team strengths is a subtraction, and neither
    depends on the order two multiplications happened in.

    Combining two Uncertainties does not stay exact — quadrature leaves the
    rationals at the first square root — and neither does the folded-normal mean,
    which needs ``exp`` and ``erf``. So the crossing exists, and it is here, alone,
    so that *where does this stop being exact* has one answer and one place to be
    tested. ``tests/unit/test_pairing_invariants.py`` walks the package to keep it
    the only one.
    """

    return float(value)


@final
@dataclass(frozen=True)
class Side:
    """One side of a match: what it plays like, and how sure that is.

    ``strength`` is on the Level scale and stays exact. ``sigma`` is the
    Uncertainty of that strength and is a ``float``, because combining two of them
    is where exactness ends — the type says so rather than a comment saying so.
    """

    strength: Level
    sigma: float


def side_of_one(player: PlayerSkill) -> Side:
    """A team of one is that player.

    The singles path, and the base case doubles reduces to: nothing about a side
    of one is a pairing decision, so tennis and squash reach the same forecast
    arithmetic without a meaningless pairing step in front of it.
    """

    return Side(strength=player.level, sigma=as_float(player.uncertainty))


def combine_uncertainty(left: float, right: float) -> float:
    """Two independent uncertainties, combined in quadrature.

    The single place this engine is allowed to combine two standard deviations,
    and it is applied to the *gap between two sides* rather than to a roster.
    """

    return math.sqrt(left * left + right * right)


def expected_absolute_gap(mean: float, spread: float) -> float:
    """``E|X|`` for ``X ~ N(mean, spread)`` — the folded-normal mean.

    At ``spread == 0`` this is ``|mean|`` exactly, which is the case a test can
    check against arithmetic anybody can do by hand. Above it the value rises,
    and it never falls below ``|mean|``: the platform's own uncertainty about two
    players is a reason to expect a *less* even match, never a more even one.
    """

    magnitude = abs(mean)
    if spread <= 0.0:
        return magnitude
    scaled = magnitude / spread
    density = spread * _SQRT_TWO_OVER_PI * math.exp(-0.5 * scaled * scaled)
    return density + magnitude * math.erf(scaled / math.sqrt(2.0))


def absolute_gap_deviation(mean: float, spread: float) -> float:
    """The standard deviation of ``|X|`` — how wrong the reported gap could be.

    ``Var|X| = mean² + spread² − E|X|²``, which is exactly zero when the platform
    is certain and rises with σ. This is the quantity the margin is made of, and
    it is why a forecast between two freshly-onboarded players reports a number
    the card then declines to print rather than a confident one.

    Floored at zero before the root: the identity is exact in real arithmetic and
    the subtraction of two nearly-equal floats is not, so a roster at the σ floor
    can otherwise produce a variance of ``-1e-17`` and a ``ValueError`` from a
    domain error nobody has.
    """

    expected = expected_absolute_gap(mean, spread)
    variance = mean * mean + spread * spread - expected * expected
    return math.sqrt(max(0.0, variance))


def round_half_away_from_zero(value: float) -> int:
    """The one rounding rule in the engine, stated once.

    Python's ``round`` is half-to-even, which sends 78,5 to 78 and 79,5 to 80 —
    two neighbouring forecasts rounded in opposite directions, for no reason a
    player could be told. Away from zero is symmetric in sign and gives the same
    answer for the same magnitude whichever way the gap runs.
    """

    magnitude = abs(value)
    whole = int(magnitude)
    if magnitude - whole >= 0.5:
        whole += 1
    return -whole if value < 0 else whole
