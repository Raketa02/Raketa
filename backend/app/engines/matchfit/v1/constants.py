"""Match Fit v1's constants — the weight table, and five numbers beside it.

Constants travel with the version as a frozen dataclass and every one of them
carries, as its docstring, the measurement that would falsify it (``docs/adr/0015``,
``docs/adr/0022``). A constant with no such measurement is a preference wearing a
number's clothes, and retuning it is then taste rather than science.

**The table is complete, and the arithmetic that said so while it was not is still
here.** ``PENDING_WEIGHTS`` named the terms ADR-0027 specified and this engine had
not built, and the constants refuse to be built unless the declared weights and the
pending ones sum to **exactly 100**. Completing the table was exactly the diff that
promise described: two lines moved from one mapping to the other, and
``PENDING_WEIGHTS`` is now empty. It stays — as an empty mapping and a guard that
still runs — because the next lineage that owes a term should owe it in arithmetic
rather than in a comment, and because *the weights sum to 100* is now enforced in
the unqualified form the spec asks for.

**Viability is a probability, and the three constants below it are the parts of
one.** *Will this match be played* is not a taste, a preference or a fit — it is a
frequency, and the platform is right or wrong about it in a way that can be counted:
take every match a player joined, bucket them by the viability the engine gave them,
and measure the share that were actually played. That single measurement falsifies
all three numbers at once and is what a blend of scores could never have offered,
which is the reason the term composes as a product of two probabilities rather than
as a weighted average of two marks.

**Time fit and travel are two terms and used to be one number.** The source design
labelled a single term *"Time and travel"* and then computed only the travel half,
so *when a player said they could play* — the first thing anybody actually filters
on — carried weight in the table and no arithmetic anywhere. The 20 points are now
split 12 to time and 8 to travel, as two terms that move independently, and the two
halves of a decision that were never separable are separately falsifiable.

**Coverage is measured against the declared weights alone**, never against 100.
That distinction is now invisible, because the declared weights *are* 100 — and it
is the reason the rule was worth stating while they were not. Weight belonging to a
term nobody has built is not evidence the platform is missing about a match, and
counting it would have turned Coverage into a report on the engine's completeness.
The consequence is that Coverage means something slightly different in this version
than in the three before it: a score of 100% coverage here is a claim about ten
terms and was a claim about six. That is what every score carrying its engine
version is for, and it is why no historical score needs restating.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, final

from app.engines.fit import TermCode
from app.engines.matchmaking import HOLD_LADDER, CourtHold
from app.kernel import Minutes, Ratio, invariant, minutes, ratio

#: This lineage, permanently. It travels on every score, because a constant below
#: can only be falsified against results it can be attributed to.
ENGINE_VERSION = "matchfit-v1"

#: The terms the table still owes, with the weight each will take. **Empty**, for
#: the first time: every term ADR-0027 specifies is now built and weighted below.
#:
#: A weight belongs here rather than in ``weights`` while the term behind it does
#: not exist, because it would otherwise be a denominator with nothing in the
#: numerator — lowering every Coverage figure by the same amount and saying nothing
#: about any match. The mapping and the guard that reads it survive the table being
#: complete, so a later lineage adding an eleventh term declares the debt in
#: arithmetic rather than in a comment.
PENDING_WEIGHTS: Mapping[str, int] = MappingProxyType({})

#: What the ten weights must sum to. Not a hypothesis — it is what makes a weight
#: readable as a share of the score rather than as an arbitrary magnitude.
WEIGHT_TOTAL = 100


@final
@dataclass(frozen=True)
class MatchFitConstants:
    """The v1 hypotheses: ten weights, three decay spans, three mismatch values, the
    three parts of a viability, and a threshold."""

    weights: Mapping[TermCode, int] = field(
        default_factory=lambda: MappingProxyType(
            {
                TermCode.SKILL_OVERLAP: 24,
                TermCode.PREDICTED_BALANCE: 14,
                TermCode.TIME_FIT: 12,
                TermCode.MATCH_VIABILITY: 12,
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

    overlap_span: Ratio = field(default_factory=lambda: ratio(110, 100))
    """How far from the Level a match is aimed at overlap decays to nothing, **in
    Level points**.

    **A full Band, and that is a claim borrowed rather than invented.** The rating
    context prints four plain-language bands and the two widest — Established
    2,7–3,8 and Advanced 3,9–5,0 — each span 1,10. So a player a span away from
    what a match is aimed at is one the platform would describe with a *different
    word*, and the point at which the word changes is the point at which *this
    match is for you* has nothing left to say. It is the same argument the pairing
    engine's ``gap_clamp`` makes about a gap between two sides, pointed at a
    distance from a target instead.

    **The band widths are the rating context's and are deliberately copied rather
    than imported**, exactly as the pairing engine copies the onboarding σ floor: a
    Match Fit score must not move because a rating lineage retuned, and the
    falsification programme rests on being able to attribute a number to one
    lineage. An AST walk keeps this package from reaching for that one, and a
    mirrored assertion in the **persona** suite — where a literal belongs, beside
    the pairing engine's copy of the onboarding σ floor — keeps the copy honest, so
    a re-cut of the bands turns this derivation red instead of silently
    invalidating it.

    **Symmetric, and no second constant for the direction.** Being a Level too
    strong for a match and a Level too weak are both *not the match you belong in*,
    and splitting them would be a second number with an ordering between the two
    that nothing here could settle. The payload carries both Levels, so a client
    can say *above* or *below* without the score encoding it.

    **One span for both resolutions**, whether the target came from the exact Seat
    target or from a Target band's midpoint. A tolerance that widened with the band
    was the alternative and is the failure this spec exists to remove wearing a new
    suit: it would score a match with three seats open at full marks for everybody
    and the same match with one seat open honestly, so the emptier match — the one
    the platform knows least about — would win.

    **Falsified by:** the Level of the players who actually join, against the target
    that was advertised when they were shown the card. Bucket joins by distance from
    the target; the distance at which the join rate reaches the rate for matches
    nobody is aimed at is where this span belongs. Sharper, once matches have been
    played: the same buckets against the result margin, which says whether a player
    a span away actually had a bad evening or merely a different card.
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

    hold_confidence: Mapping[CourtHold, Ratio] = field(
        default_factory=lambda: MappingProxyType(
            {
                CourtHold.NONE: ratio(0, 1),
                CourtHold.SOFT: ratio(50, 100),
                CourtHold.HARD: ratio(100, 100),
            }
        )
    )
    """The chance each rung of the hold ladder still has a court at match time.

    A probability, one per rung, and the three are chosen as the three answers to
    *has the court been secured?* — **no** (nobody has one yet), **maybe** (a
    provisional hold that can lapse), **yes** (booked, and the club has committed
    it). A hard hold at one is the claim that a booking is kept, which is what makes
    the club's crowding stop mattering the moment a court is actually yours: the
    court you have cannot be taken by the club being busy.

    **The ordering is guarded and the values are not.** *A firmer hold never makes a
    match less likely* is the domain's claim and it survives any retune, because the
    guard below walks ``HOLD_LADDER`` and refuses a mapping that falls; how far apart
    the rungs sit is the hypothesis.

    **Falsified by:** the share of matches at each rung, measured at the same point
    in their run-up, that were played — and, for the middle rung specifically, the
    share of soft holds that lapsed. If soft holds almost never lapse the middle rung
    belongs near the top and the ladder is nearly a bool; if a hard hold is lost as
    often as a soft one, the ladder is not the thing that predicts a court at all.
    """

    seat_fill_ceiling: Ratio = field(default_factory=lambda: ratio(50, 100))
    """The best chance an unpaid seat has of being paid before the cutoff.

    A ceiling, and **below one on purpose**: with all the time in the world, an
    empty seat is a coin flip and never a certainty. Without it the arithmetic would
    say that a match nobody has joined is as likely to be played as a full one so
    long as it is early enough, which is *absence flattering* in a new suit — the
    exact failure ADR-0027 exists to remove, reintroduced by the term that was
    supposed to close it.

    **Falsified by:** the share of unpaid seats that were eventually paid, measured
    at more than a full ``fill_window`` before the cutoff so the run-up cannot
    confound it. That share *is* this number; it is the one constant here whose
    measurement needs no bucketing at all.
    """

    fill_window: Minutes = field(default_factory=lambda: minutes(720))
    """How long an unpaid seat needs before the cutoff for its chances to be full.

    Half a day. Inside it the chance an empty seat fills runs down to nothing at the
    cutoff, on the same straight decay every other numeric term here uses, so *how
    long is left* is a quantity rather than a cliff: a match at five minutes to the
    cutoff with a seat open is not the same recommendation as one at five hours.

    Absolute rather than a share of the time since the match was created, for
    travel's reason pointed at the clock: a share would give a match posted a month
    ahead a fill window of days and one posted this morning a window of minutes,
    punishing hardest exactly the matches that are filling fastest.

    **Falsified by:** unpaid seats bucketed by minutes remaining, against the share
    of them that were eventually paid. The point where that curve flattens is where
    this window belongs; if it is flat everywhere, the run-up does not predict
    filling and the term should read the cutoff no further than as a filter.
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
            ("the seat fill ceiling", self.seat_fill_ceiling),
        ):
            invariant(0 <= value < 1, f"{named} is not below full marks: {value}")
        invariant(self.overlap_span > 0, f"an overlap span of {self.overlap_span}")
        invariant(self.price_decay_span > 0, f"a price span of {self.price_decay_span}")
        invariant(
            self.travel_decay_span > 0, f"a travel span of {self.travel_decay_span}"
        )
        invariant(self.fill_window > 0, f"a fill window of {self.fill_window}")
        invariant(
            0 < self.reasons_returned, f"{self.reasons_returned} reasons returned"
        )
        # The hold ladder, in the vocabulary's order and not in this mapping's.
        # A retune is free to move the rungs and not free to let a firmer hold
        # predict a match *less* likely to be played — which is the claim the
        # viability property test asserts and which no retune may invert.
        invariant(
            set(HOLD_LADDER) == set(CourtHold) and len(HOLD_LADDER) == len(CourtHold),
            f"the hold ladder {[rung.value for rung in HOLD_LADDER]} is not the "
            f"vocabulary's {[rung.value for rung in CourtHold]}",
        )
        invariant(
            set(self.hold_confidence) == set(CourtHold),
            f"the ladder scores {sorted(rung.value for rung in self.hold_confidence)}, "
            f"the vocabulary names {sorted(rung.value for rung in CourtHold)}",
        )
        rungs = [self.hold_confidence[rung] for rung in HOLD_LADDER]
        for lower, higher in zip(rungs, rungs[1:], strict=False):
            invariant(
                lower <= higher,
                f"the hold ladder falls: {rungs}",
            )
        for rung, chance in self.hold_confidence.items():
            invariant(0 <= chance <= 1, f"{rung.value} hold outside 0..1: {chance}")


#: The v1 constants, frozen. One instance, so a caller cannot hold a retuned copy.
CONSTANTS = MatchFitConstants()
