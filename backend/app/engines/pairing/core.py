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

In doubles that propagation happens **twice, through the team weights**: a team
strength is ``w·L_weak + (1−w)·L_strong``, so its uncertainty is
``√((w·σ_weak)² + ((1−w)·σ_strong)²)`` — each partner's σ scaled by the weight
their Level was actually given — and the two team uncertainties then combine into
the gap. Both steps are the same one quadrature rule, applied to the quantity
being formed rather than to the people in it. That is also why doubles is
forecast *more* confidently than singles between the same players: averaging two
independent estimates is what a team strength is.

**The seat target is solved, not searched.** A team strength is piecewise-linear
in the joiner's Level with a single kink where the joiner overtakes their partner,
so *which Level would even this match* is one comparison and one division per
arrangement, in exact rationals. That is why ``even_partner_level`` is here beside
the strength it inverts: the two are the same line read in opposite directions,
and a version that retuned one without the other would advertise a seat it could
not then forecast as even.

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
from app.kernel import Ratio, invariant, ratio

#: ``√(2/π)``, the folded-normal mean's coefficient at a mean of zero. Named
#: because it is arithmetic rather than a hypothesis: retuning it would not
#: retune a product decision, it would make the expectation wrong.
_SQRT_TWO_OVER_PI = math.sqrt(2.0 / math.pi)

#: The complete enumeration of the ways four seats divide into two pairs, as seat
#: indices. **Three, and that is a proof rather than a list:** fix the player on
#: the first seat, choose their partner from the remaining three, and the other
#: two are decided by having nowhere else to go. So there is no fourth
#: arrangement to miss, no heuristic, and no sampling — the engine searches all of
#: them, in constant time, and ``test_pairing_invariants`` derives the same three
#: partitions from scratch to keep this list honest.
SPLITS: tuple[tuple[tuple[int, ...], tuple[int, ...]], ...] = (
    ((0, 1), (2, 3)),
    ((0, 2), (1, 3)),
    ((0, 3), (1, 2)),
)


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


def side_of_two(
    first: PlayerSkill, second: PlayerSkill, *, weaker_weight: Ratio
) -> Side:
    """A team of two: **not the average of the two Levels.**

    The blend is ``w·L_weak + (1−w)·L_strong`` with ``w`` above a half, because
    the weaker side is attacked — a 4,5 partnered with a 2,0 does not play like a
    3,25, it plays like whatever the 2,0 can return. ``w`` is the caller's, a
    per-sport constant, so *how much* more the weaker partner counts is a
    measurement rather than a rewrite.

    The strength stays **exact**: two ``Ratio`` multiplications and one addition,
    so the gap between two team strengths does not depend on the order the
    multiplications happened in. The uncertainty does not, and the type says so —
    each partner's σ is scaled by the weight their Level was given and the two are
    combined in quadrature, which is ``Var(w·X + (1−w)·Y)`` for independent
    estimates and is the same one rule the gap itself uses.

    **Which partner is the weaker one is decided on Level, and an exact tie is
    broken on Uncertainty rather than on seat order.** At equal Levels the blend
    is the same number either way and only the σ weighting can differ — but *seat
    order* is who pressed join first, and a team whose forecast depends on that is
    one where reseating the same four people changes the match. The tie goes to
    the player the platform is *least* sure of, which is the assignment that
    produces the wider team σ of the two available: when it genuinely cannot tell
    which of two equal players is the weaker one, it does not get to pick the
    reading that makes it look more certain. Equal Levels *and* equal σ leaves
    nothing to break, because both orderings then give the same side.
    """

    weaker, stronger = _weaker_first(first, second)
    stronger_weight = Ratio(1 - weaker_weight)
    return Side(
        strength=Level(
            Ratio(weaker_weight * weaker.level + stronger_weight * stronger.level)
        ),
        sigma=combine_uncertainty(
            as_float(Ratio(weaker_weight * weaker.uncertainty)),
            as_float(Ratio(stronger_weight * stronger.uncertainty)),
        ),
    )


def _weaker_first(
    first: PlayerSkill, second: PlayerSkill
) -> tuple[PlayerSkill, PlayerSkill]:
    """The two partners, weaker one first. See ``side_of_two`` for the tie."""

    if first.level != second.level:
        return (first, second) if first.level < second.level else (second, first)
    return (
        (first, second) if first.uncertainty >= second.uncertainty else (second, first)
    )


def even_partner_level(
    partner: Level, opposing: Level, *, weaker_weight: Ratio
) -> Level:
    """The Level that, sat next to ``partner``, makes the two sides exactly equal.

    Team strength as a function of the joiner's Level ``t`` is
    ``w·min(t, L) + (1−w)·max(t, L)`` for a partner at ``L`` — two straight lines
    meeting at ``t = L``, with the steeper one below it, since the weaker partner
    counts for more. It is continuous, strictly increasing and unbounded in both
    directions, so ``strength(t) = opposing`` has **exactly one** solution and it
    is found by picking the piece rather than by searching for it.

    Which piece is decided by a single comparison: the two lines meet at
    ``strength(L) = L``, so an opposing side weaker than the partner needs a
    joiner below them and an opposing side stronger needs one above.

    **Exact.** Two multiplications, a subtraction and a division over ``Ratio``,
    so the answer is a rational and not the nearest point of somebody's grid. The
    resolution of a scan is a property of the scan, and a seat target that moves
    when the step size changes is reporting the step size.
    """

    stronger_weight = Ratio(1 - weaker_weight)
    if opposing <= partner:
        return Level(Ratio((opposing - stronger_weight * partner) / weaker_weight))
    return Level(Ratio((opposing - weaker_weight * partner) / stronger_weight))


def evening_levels(
    seated: tuple[PlayerSkill, ...], *, weaker_weight: Ratio
) -> tuple[Level, ...]:
    """One Level per seated player: what would even the match beside *them*.

    Three seated players admit three arrangements of the fourth seat — the joiner
    partners one of the three and plays the other two — and each arrangement is
    evened by its own Level. So the objective a seat target minimises, the gap the
    *chosen* split would report, is the lowest of three piecewise-linear
    functions of the joiner's Level, and each of the three touches zero exactly
    once. Its minimum is therefore zero and the minimising set is these Levels:
    there is no search, and there is nothing a finer grid would find.

    Returned in seated order, and the caller chooses between them.
    """

    return tuple(
        even_partner_level(
            candidate.level,
            side_of_two(*_others(seated, index), weaker_weight=weaker_weight).strength,
            weaker_weight=weaker_weight,
        )
        for index, candidate in enumerate(seated)
    )


def _others(
    seated: tuple[PlayerSkill, ...], index: int
) -> tuple[PlayerSkill, PlayerSkill]:
    """The two the joiner would be playing, if they partnered ``seated[index]``."""

    first, second = (
        player for position, player in enumerate(seated) if position != index
    )
    return first, second


def middle_level(levels: tuple[Level, ...]) -> Level:
    """The median of an odd number of Levels — which of several answers to give.

    Every Level in ``evening_levels`` produces an exactly even match, so *as even
    as possible* does not choose between them and something has to. The outer two
    are the answers that require the joiner to be the odd one out: partnering the
    **strongest** seated player needs somebody well below everybody there, and
    partnering the **weakest** needs somebody well above. Only the middle answer
    is guaranteed to fall inside the Levels already in the match, and that is what
    is advertised — a seat aimed at a Level nobody in the match is near is a seat
    nobody reading the card will recognise as theirs.

    It is also the rule that has nothing to break: a median of three is defined
    with duplicates and needs no anchor, no distance and no tie-break, so no part
    of the answer is decided by seat order or by which end a scan started from.
    The grid this replaces took the lowest of the tying candidates, which is the
    *outer* answer and an artefact of scanning upwards.
    """

    invariant(len(levels) % 2 == 1, f"no middle of {len(levels)} levels")
    return sorted(levels)[len(levels) // 2]


def mean_level(levels: tuple[Level, ...]) -> Level:
    """The mean of at least one Level, exactly. The centre of a target band."""

    # `len(...) > 0` rather than the tuple itself: `invariant` breaks on `None`
    # and `False` and on nothing else, deliberately, so an empty tuple sails
    # straight through it and the division below is what fails instead.
    invariant(len(levels) > 0, "the mean of no levels")
    return Level(Ratio(sum(levels, ratio(0, 1)) / len(levels)))


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
