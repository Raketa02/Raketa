"""The Match Fit core — everything that must outlive a version.

A version directory owns the *constants*: the weights, the spans a decay runs over,
what a mismatch is worth, the threshold a warning fires at. This module owns the
*mechanism* those constants feed, extracted now so that a later lineage cannot
develop a second idea of what a term's absence means.

**The kind of a term is a fact about how it was built, not a label on it.** There
are exactly two builders below, and between them they are the whole of ADR-0027's
repair:

* ``constraint_term`` always returns a ``ScoredTerm``. There is no path from it to
  an exclusion, so *a constraint term is never excluded* is unwritable rather than
  reviewed for. An undeclared limit reaches it as ``FULL_MARKS``, which is what
  *no limit* means.
* ``evidence_term`` takes an **optional** value and returns an ``ExcludedTerm`` when
  it is absent. There is no default to write in its place — ``ExcludedTerm`` has no
  value field — so absent evidence cannot be spelled as a good score even by a
  careless call site.

**Renormalisation is the mechanism, so the score is computed through it.** The
weights of the terms that ran are rescaled to sum to exactly one and the score is
the sum of share times value. That is why ``renormalise`` is a function producing
the number rather than a claim asserted about it: *the renormalised weights sum to
one* is then a test of the arithmetic the engine actually ran.

It also means the score is a **weighted average over what ran**, and that has a
consequence worth stating out loud, because it is the one thing about this design
that surprises everybody: excluding a term whose value was *below* the average
**raises** the average. Absence is still never allowed to flatter — an exclusion can
never do better than including that term at full marks, which is a property test —
but exclusion is not monotone downwards, and it cannot be. That is precisely why
Coverage is reported as its own number instead of being folded in: the pair *(fit,
coverage)* is the honest statement, and either one alone is not.

**Exact until the last step.** A value is a ``Ratio`` over two integers, a weight is
an ``int``, so the weighted average is an exact rational and there is no float
anywhere in this engine. The single crossing is ``whole_percent``, which is also the
one rounding rule — stated once, here, rather than at the two call sites that want
a percentage.

**The pairing engine is not imported, in either direction.** ``.importlinter`` forbids
it both ways and the purity-gate suite proves the contract fires. What this engine
*does* import is the kernel, as every engine does — including, since #88, the one
rounding rule, which lived here in a third copy until ADR-0022's two questions were
put to it. The fence forbids this engine's arithmetic from moving when the *pairing
version* moves; a kernel rule carries no version and no tuning knob, so there is no
retune for it to transmit, and the alternative was a fourth copy the next time an
engine needed a percentage.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import final

from app.engines.fit import (
    ExcludedTerm,
    ScoredTerm,
    Term,
    TermCode,
    TermFact,
    TermKind,
)
from app.kernel import Ratio, invariant, ratio, round_half_away_from_zero

#: A term with nothing held against it. What an **undeclared** limit scores, and
#: the only value a constraint term reaches when the player said nothing at all.
FULL_MARKS: Ratio = ratio(1, 1)

#: A term scoring nothing — the floor of a decay, and never an exclusion. A term at
#: zero *ran*: the platform looked, and the answer was bad. That is a different fact
#: from not having looked, and the two are different types here.
NO_MARKS: Ratio = ratio(0, 1)


def constraint_term(
    code: TermCode, weight: int, value: Ratio, fact: TermFact
) -> ScoredTerm:
    """A limit the player declared. **Always scores; never excluded.**

    An undeclared limit is genuinely no limit, so the term keeps its weight, scores
    ``FULL_MARKS`` and leaves Coverage exactly where it was. That is the intent
    pool's partial-profile rule — *a missing price ceiling means eligible at any
    price* — and it is the half of ADR-0027 that is **not** about absent evidence.

    The return type is the guarantee: there is no way for a constraint to become an
    exclusion, so nothing can quietly move a declared limit onto the evidence side
    and make a silent player's matches score thinly.
    """

    return ScoredTerm(
        code=code, kind=TermKind.CONSTRAINT, weight=weight, value=value, fact=fact
    )


@final
@dataclass(frozen=True)
class Observed:
    """What an evidence term found: a value in 0..1, and the quantities behind it.

    **The two arrive together or not at all**, which is the same rule the rating
    context states as *a rating is never only a number*. An evidence term either
    observed something — and can therefore say what — or observed nothing, and then
    there is no value to report and no payload describing it. Spelling that as one
    optional argument rather than two makes *a score with no payload* and *a payload
    with no score* unwritable, instead of two invariants somebody has to keep.
    """

    value: Ratio
    fact: TermFact

    def __post_init__(self) -> None:
        invariant(0 <= self.value <= 1, f"an observation outside 0..1: {self.value}")


def evidence_term(code: TermCode, weight: int, observed: Observed | None) -> Term:
    """Something the platform observed. **Absent evidence is excluded, never good.**

    The optional observation is the mechanism and the whole of it: with nothing
    observed there is no number to score, so the term drops out and the surviving
    weights carry the score between them. The alternative — the one this spec exists
    to remove — is a friendly default, and a default is indistinguishable from an
    observation the moment it is written down.
    """

    if observed is None:
        return ExcludedTerm(code=code, weight=weight)
    return ScoredTerm(
        code=code,
        kind=TermKind.EVIDENCE,
        weight=weight,
        value=observed.value,
        fact=observed.fact,
    )


def decayed(beyond: Ratio, span: Ratio) -> Ratio:
    """Full marks up to a declared limit, then straight down over ``span``.

    The one curve every constraint term with a *numeric* limit shares — price
    against a ceiling, travel against a radius — so the shape is stated once and a
    version tunes only how far the decay runs. ``beyond`` is how far past the limit
    this match is, in the limit's own units, and is never negative: a match inside
    the limit is not *negatively* beyond it, it is simply within, and clamping that
    at the call site would let a cheap match score above full marks.

    **It never reaches exclusion.** The floor is ``NO_MARKS`` and a term at zero is
    still a term that ran, with its weight in the denominator and its quantities in
    its payload. Price and distance are conditions and never rejections: the intent
    pool's rules are explicit that *nothing is ever excluded on distance*, so a
    match past the radius reaches the player as a lower score rather than as an
    absence they cannot argue with.

    A ``span`` of zero is the limit case of a limit with no tolerance at all, and it
    is handled by the ordering of the two comparisons rather than by a guard: with
    nothing beyond the limit the answer is full marks, and otherwise ``beyond`` is
    at least as large as the span, so the floor answers and nothing divides by zero.
    """

    invariant(beyond >= 0, f"a decay from {beyond} inside the limit")
    invariant(span >= 0, f"a decay over a span of {span}")
    if beyond == 0:
        return FULL_MARKS
    if beyond >= span:
        return NO_MARKS
    return Ratio(1 - beyond / span)


def renormalise(scored: tuple[ScoredTerm, ...]) -> tuple[Ratio, ...]:
    """The weights of the terms that ran, rescaled to sum to exactly one.

    Exact, because the weights are integers: the shares are rationals summing to
    ``1`` and not to ``0.9999999999999999``, so *the renormalised weights sum to
    one* is an equality a test can assert rather than a tolerance it has to pick.

    This is the mechanism the score is computed **through** rather than a
    description of it. Two matches scoring the same fit may have been scored over
    different term sets, which is the real cost of renormalising and is the reason
    Coverage exists — it makes that visible; it does not make it go away.
    """

    total = sum(term.weight for term in scored)
    invariant(total > 0, "renormalising over no weight at all")
    return tuple(ratio(term.weight, total) for term in scored)


def weighted_value(scored: tuple[ScoredTerm, ...]) -> Ratio:
    """The score, before it becomes a percentage: shares times values, summed.

    Exactly the weighted average of the terms that ran. Nothing is added to it, and
    that is the point of building it here rather than in the engine: a bonus, a
    penalty or a coverage adjustment applied on the way out would have to be
    written into this line, where it is one addition away from every reader.
    """

    shares = renormalise(scored)
    return Ratio(
        sum(
            (share * term.value for share, term in zip(shares, scored, strict=True)),
            ratio(0, 1),
        )
    )


def measured_share(terms: tuple[Term, ...]) -> Ratio:
    """Coverage, before it becomes a percentage: the weight that ran, over all of it.

    The denominator is every weight in the table, scored and excluded alike, so this
    answers *how much of the score was actually measured* and nothing else. Weight
    that does not exist yet is not in the tuple and therefore not in the
    denominator: a term nobody has built is not evidence the platform is missing
    about this match, and counting it would make Coverage a report on the engine's
    completeness rather than on the match's.
    """

    total = sum(term.weight for term in terms)
    invariant(total > 0, "coverage over no weight at all")
    ran = sum(term.weight for term in terms if isinstance(term, ScoredTerm))
    return ratio(ran, total)


def ranked_by_contribution(scored: tuple[ScoredTerm, ...]) -> tuple[ScoredTerm, ...]:
    """The terms that ran, strongest **contributor** first.

    Ranked on weight times value and never on value alone: a term scoring 1,0 out of
    a weight of 3 explains less about why this match is good than one scoring 0,8 out
    of 24, and a reason list ordered by value would open with the smallest true thing
    it could find.

    The ordering is unchanged by renormalisation — every share is the same weight
    over the same total — so *which* reasons a card shows does not move when a term
    is excluded elsewhere in the table.

    Sorting is **stable**, so two terms the engine genuinely cannot separate stay in
    table order rather than in whichever order the last sort happened to leave them.
    """

    return tuple(sorted(scored, key=lambda term: -term.contribution))


def lowest_contribution(scored: tuple[ScoredTerm, ...]) -> ScoredTerm:
    """The weakest contributor — the one term a warning can ever be about.

    ``min`` and not ``ranked_by_contribution()[-1]``: the two agree on the value and
    not on the tie. A stable descending sort leaves the *last* of several tied terms
    at the end, while ``min`` returns the *first* in table order, which is the same
    tie-break the reasons use. One rule for ties, in both directions.
    """

    invariant(len(scored) > 0, "the lowest contributor of no terms")
    return min(scored, key=lambda term: term.contribution)


def whole_percent(value: Ratio) -> int:
    """A ratio in 0..1 as a whole percent, rounded half away from zero.

    **The one crossing out of exact arithmetic, and the one rounding rule.** Both
    numbers this engine reports go through here, so a fit of 84 and a coverage of 63
    cannot have been rounded by two different rules.

    Half away from zero rather than Python's half-to-even, which sends 78,5 to 78
    and 79,5 to 80 — two neighbouring scores rounded in opposite directions for no
    reason a player could be told. **The rule itself is the kernel's** (#88), not
    restated here: what this function owns is the scaling and the range it will
    accept, which is engine vocabulary, and the rounding underneath is arithmetic
    that has exactly one home.

    The range guard is not decoration. Every ratio reaching here is a renormalised
    weighted average of values that are themselves in 0..1, so a value outside that
    range means the renormalisation is wrong, and the caller would otherwise print
    a fit of 104 rather than raise.
    """

    invariant(0 <= value <= 1, f"a percentage of {value}")
    return round_half_away_from_zero(Fraction(value) * 100)
