"""Match Fit v1's constants — the weight table, and five numbers beside it.

Constants travel with the version as a frozen dataclass and every one of them
carries, as its docstring, the measurement that would falsify it (``docs/adr/0015``,
``docs/adr/0022``). A constant with no such measurement is a preference wearing a
number's clothes, and retuning it is then taste rather than science.

**The table is incomplete, and it says so in arithmetic rather than in a comment.**
Three of the ten terms ADR-0027 specifies are not built yet, so their weights are
written out in ``PENDING_WEIGHTS`` with the issue that lands each one, and the
constants refuse to be built unless the declared weights and the pending ones sum to
**exactly 100**. So the spec's *"the weights sum to 100"* is enforced today, in the
only form in which it can be true today, and completing the table is a diff that
moves a line from one mapping to the other.

**Time fit and travel are two terms and used to be one number.** The source design
labelled a single term *"Time and travel"* and then computed only the travel half,
so *when a player said they could play* — the first thing anybody actually filters
on — carried weight in the table and no arithmetic anywhere. The 20 points are now
split 12 to time and 8 to travel, as two terms that move independently, and the two
halves of a decision that were never separable are separately falsifiable.

**Coverage is measured against the declared weights alone**, never against 100.
Weight belonging to a term nobody has built is not evidence the platform is missing
about a match — a match cannot be blamed for an unwritten term — and counting it
would turn Coverage into a report on the engine's completeness. The consequence is
that Coverage means something slightly different before and after each of the four
tickets below, which is why every score carries the engine version that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, final

from app.engines.fit import TermCode
from app.kernel import Minutes, Ratio, invariant, minutes, ratio

#: This lineage, permanently. It travels on every score, because a constant below
#: can only be falsified against results it can be attributed to.
ENGINE_VERSION = "matchfit-v1"

#: The three terms the table still owes, with the weights ADR-0027 assigns them and
#: the issue that lands each. They are here rather than in ``weights`` because a
#: weight with no term behind it is a denominator with nothing in the numerator: it
#: would lower every Coverage figure by the same amount and say nothing about any
#: match.
#:
#: * ``skill_overlap`` 24 and ``predicted_balance`` 14 — #86. Both read the pairing
#:   analysis this engine already takes, which is why the analysis is an input from
#:   the first commit rather than an argument added later.
#: * ``match_viability`` 12 — #85. Evidence, and the only evidence term that is
#:   *always* computable, because every match has a phase and a court hold state.
PENDING_WEIGHTS: Mapping[str, int] = MappingProxyType(
    {
        "skill_overlap": 24,
        "predicted_balance": 14,
        "match_viability": 12,
    }
)

#: What the ten weights must sum to. Not a hypothesis — it is what makes a weight
#: readable as a share of the score rather than as an arbitrary magnitude.
WEIGHT_TOTAL = 100


@final
@dataclass(frozen=True)
class MatchFitConstants:
    """The v1 hypotheses: seven weights, two decay spans, three mismatch values, and
    a threshold."""

    weights: Mapping[TermCode, int] = field(
        default_factory=lambda: MappingProxyType(
            {
                TermCode.TIME_FIT: 12,
                TermCode.GROUP_RELIABILITY: 11,
                TermCode.TRAVEL: 8,
                TermCode.LADDER_QUALIFICATION: 6,
                TermCode.PRICE: 6,
                TermCode.MATCH_TYPE: 4,
                TermCode.FAMILIARITY: 3,
            }
        )
    )
    """How much of the score each term is worth, out of a hundred.

    In descending weight, which is also the order terms appear in a result and
    therefore the tie-break for the reason ranking — so two terms that contributed
    exactly the same amount are ordered by which one the platform thinks matters
    more, rather than by which one happened to be scored first.

    **Falsified by:** join rate against each term's value, holding the others'
    values fixed. A weight is a claim about how much a dimension moves a decision,
    so a term whose value swings from 0,2 to 1,0 without moving the join rate is
    over-weighted, and one that flips the decision on its own is under-weighted. The
    two dark terms below cannot be measured this way until the contexts that feed
    them exist, and their weights are therefore the least defended numbers here.
    """

    price_decay_span: Ratio = field(default_factory=lambda: ratio(50, 100))
    """How far past the ceiling price decays to nothing, **as a share of it**.

    Half again: a 40 zł seat is worth nothing on this term to somebody who declared
    a 20 zł ceiling, and 30 zł is worth half. Relative rather than absolute because
    a ceiling is a statement about a budget, and budgets across this market differ
    by a factor of five — a fixed 20 zł span would leave a 100 zł-ceiling player
    scoring zero on a seat 20% over, and a 20 zł-ceiling player scoring zero at
    double.

    **Falsified by:** the joins that happen above a declared ceiling, bucketed by
    overshoot as a share of the ceiling. If a quarter of joins are at 1,5× the
    ceiling, the span is too tight and the term is hiding matches players would take;
    if joins fall off a cliff at 1,1×, it is too loose.
    """

    travel_decay_span: Minutes = field(default_factory=lambda: minutes(20))
    """How far past the declared radius travel decays to nothing, **in minutes**.

    Absolute rather than relative, which is the opposite choice to price and is
    deliberate: a minute is a minute. A proportional span would decay a
    ten-minute radius over five minutes and a sixty-minute radius over thirty,
    punishing hardest exactly the players who declared the tightest radius — which
    is the opposite of respecting a declaration.

    **Falsified by:** the same measurement pointed at minutes. Bucket joins by
    minutes past the declared radius; the point where the join rate reaches the base
    rate for matches inside the radius is where this span belongs.
    """

    time_outside: Ratio = field(default_factory=lambda: ratio(20, 100))
    """What a match outside the declared days **or** the declared hours is worth.

    **The strictest of the three mismatch values**, below the match-type mismatch
    and well below the ladder one, and that ordering is the claim. A friendly
    offered to somebody who asked for counted matches is the wrong kind of evening
    and they can still play it; a match at 07:00 offered to somebody who plays
    after work is an evening they are at work for. Not zero, because a declaration
    of *when* is a rough statement of habit rather than a calendar — a Saturday
    morning is joinable by somebody who declared weekday evenings, once — and
    because *matches outside the declaration rank lower without being hidden*.

    **One value for both halves, deliberately.** Wrong day and wrong hour are the
    same sentence — *you said you cannot play then* — so splitting them would be
    two constants and a claim about their ordering that no measurement here could
    settle. What *is* reported is which half failed, on the term's payload, so a
    client can say the true thing without the score having to encode it.

    **The rule for a match that overlaps a window only partly: the start decides.**
    A match beginning inside a declared window is inside it however long it runs,
    so a 90-minute match starting at 08:30 satisfies a declared 06:00–09:00 and
    the player reads the start time on the card. The alternative — *the whole
    match must fit* — is a defensible rule and a different snapshot: it needs a
    duration this one deliberately does not carry, so adopting it is a vocabulary
    change rather than a retune of this number.

    **Falsified by:** the join rate on matches whose start falls outside the
    declared days or hours, against matched ones at otherwise equal fit. Zero is
    falsified by any join at all. The overlap rule is falsified separately and by a
    sharper measurement: bucket matches that *start* inside a declared window by
    whether they end inside it too. If the two buckets join at materially different
    rates, the start does not decide, and the snapshot owes this term a duration.
    """

    match_type_mismatch: Ratio = field(default_factory=lambda: ratio(30, 100))
    """What a match of the wrong kind is worth to somebody who declared a kind.

    Not zero, because a counted match is still an evening of tennis: somebody who
    asked for social games and joins a counted one has played. Low, because *what
    the evening is* is the thing they declared — a friendly and a rated match are
    different activities with the same equipment.

    **Falsified by:** the join rate on mismatched matches against matched ones at
    otherwise equal fit. Zero would be falsified by any join at all; 0,30 is
    falsified if mismatched matches are joined at nearly the same rate, which would
    mean the declaration is weaker than it looks.
    """

    ladder_outside: Ratio = field(default_factory=lambda: ratio(50, 100))
    """What a non-qualifying match is worth to a player who entered a ladder.

    **Deliberately milder than a match-type mismatch.** A match that does not count
    for your ladder is the right kind of evening that simply does not count; a
    friendly offered to somebody who asked for counted matches is the wrong kind of
    evening. Half against three tenths is that ordering, and it is the ordering that
    a retune must not silently invert.

    **Falsified by:** what ladder entrants actually join. If they play qualifying and
    non-qualifying matches at similar rates, entering a ladder says less about how
    somebody chooses a match than this assumes and the value should rise; if they
    almost never join outside their ladder, it should fall.
    """

    warning_threshold: Ratio = field(default_factory=lambda: ratio(40, 100))
    """The raw value below which the weakest contributor becomes a warning.

    Read against the term's **own value** and never against its contribution, which
    is the asymmetry the spec calls for: a term can be last by contribution while
    being perfectly fine in itself — familiarity at full marks out of a weight of
    three — and warning about that would teach players to ignore warnings.

    **Falsified by:** what players do with a card that carries a warning. If warned
    matches are joined at the same rate as unwarned ones at equal fit, the warning
    is not being read and the threshold is too generous; if a warning is present on
    most cards, it has stopped being a signal, which is the same measurement from
    the other side.
    """

    reasons_returned: int = 3
    """How many reasons a score comes back with.

    A product decision rather than arithmetic — the card has room for three — but it
    is a number in the engine, so it carries a measurement like every other.

    **Falsified by:** whether a fourth reason changes a decision. Show three against
    four and compare join rates and time-to-decision; if the fourth is never the one
    players cite, three is right, and if cards with only two scored terms are
    understood as well as three, even three is generous.
    """

    def __post_init__(self) -> None:
        """What a retune of the table could silently get wrong.

        Checked once, when the constants are built, rather than at every call site
        that forms a term — this is where a retune happens, and failing at import is
        louder than failing on one home screen.
        """

        invariant(
            sum(self.weights.values()) + sum(PENDING_WEIGHTS.values()) == WEIGHT_TOTAL,
            f"the term table sums to {sum(self.weights.values())} declared plus "
            f"{sum(PENDING_WEIGHTS.values())} pending, not {WEIGHT_TOTAL}",
        )
        invariant(
            set(self.weights) == set(TermCode),
            f"the table weights {sorted(code.value for code in self.weights)}, "
            f"the vocabulary names {sorted(code.value for code in TermCode)}",
        )
        for code, weight in self.weights.items():
            invariant(weight > 0, f"{code.value} carries weight {weight}")
        for named, value in (
            ("the time outside value", self.time_outside),
            ("the match type mismatch", self.match_type_mismatch),
            ("the ladder outside value", self.ladder_outside),
            ("the warning threshold", self.warning_threshold),
        ):
            invariant(0 <= value < 1, f"{named} is not below full marks: {value}")
        invariant(
            self.price_decay_span > 0, f"a price span of {self.price_decay_span}"
        )
        invariant(
            self.travel_decay_span > 0, f"a travel span of {self.travel_decay_span}"
        )
        invariant(
            0 < self.reasons_returned, f"{self.reasons_returned} reasons returned"
        )


#: The v1 constants, frozen. One instance, so a caller cannot hold a retuned copy.
CONSTANTS = MatchFitConstants()
