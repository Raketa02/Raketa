"""Stage 4 — the three modifiers, the budget, and the one dock outside it.

Applied after the eight terms and before the quality floor, so the floor reads
the number the modifiers leave: the reliability dock exists precisely to push
somebody under it, and a floor that read the unmodified Fit would make the dock
decorative.

**Three survive, and two are struck rather than deferred.** *Language* read a
field that exists nowhere in this backend and is the nearest available proxy for
the nationality the privacy line excludes by name — ``docs/adr/0096``'s rule is
that a protected characteristic may gate and may never score, and a shared
language scores. *Intent opposition* was a second charge for a fact the intent
term already prices at 0.00, which is a gate wearing a modifier's clothes. Both
are absent from ``Modifier`` entirely, so neither can return as a row somebody
adds back without an argument.

**The budget clamps the summed stack, not each modifier**, so a stack of small
positives can never lift somebody over a recent no-show — and the reliability
floor dock sits **outside** it, derived as ``budget + 1``, which is the smallest
penalty that keeps that promise and which moves by itself if the budget ever
does.

**On day one the budget is inert and that is correct.** Calibration is the only
modifier whose input exists, so the real range is ``0 … +4`` and only in
competitive. It is standing insurance, in place before it is needed, for the same
reason the minimum-evidence gate one stage later is.
"""

from __future__ import annotations

from app.engines.matchfit.core import FamiliarityReading, Modifier, SearchMode
from app.engines.matchfit.ranking import ModifierPoints, ModifierStack
from app.engines.matchfit.ruleset import (
    BUDGETED_MODIFIERS,
    ModifierRules,
    Ruleset,
    TagRules,
)
from app.engines.matchfit.scorable import (
    ModifierFacts,
    ScorableCandidate,
    Searcher,
    SharedHistory,
)
from app.kernel import invariant

#: A modifier either fired or it did not. **Not firing is spelled ``None`` and
#: never zero**, on the rule the terms run on one stage earlier: a zero is a
#: measurement, and a modifier worth nothing is absent from the stack rather than
#: present at nothing.
ModifierOutcome = ModifierPoints | None


def calibration_value(
    searcher: Searcher, facts: ModifierFacts, ruleset: Ruleset
) -> ModifierOutcome:
    """Whether this pairing is worth extra to somebody's rating settling.

    **Binary, not a ramp.** ``calibration_priority`` on the rating aggregate has
    two values, so a 0…+4 range read off it is 0 or +4 and nothing between — the
    input document's ramp describes a field that does not exist.

    **Competitive only**, because it applies where a rating is at stake and a
    for-fun game is never counted. And it **prints**, because a player is
    entitled to know when they are being matched partly for somebody else's
    benefit.
    """

    if searcher.mode is not SearchMode.COMPETITIVE or not facts.calibration_elevated:
        return None
    return ModifierPoints(
        modifier=Modifier.CALIBRATION_VALUE,
        points=float(ruleset.modifiers.ranges[Modifier.CALIBRATION_VALUE].maximum),
    )


def familiarity(
    searcher: Searcher, facts: ModifierFacts, ruleset: Ruleset
) -> ModifierOutcome:
    """A shared history, signed by what the **searcher** said they are here for.

    ``strength = 0.5 ^ (days / half_life) × (1 − φⁿ)``, and the sign comes from
    :func:`reading_for`. A repetition-seeker takes the range's positive arm and a
    variety-seeker its negative one; a reader whose tags say neither falls to
    ``default_lean`` of the negative arm — *mildly novelty-preferring*.

    **The arm is asymmetric on purpose** and it is the same rule the clash cap
    is: being wrong about a positive costs a duller evening, and being wrong
    about a negative buries a person.
    """

    if facts.shared_history is None:
        return None
    rules = ruleset.modifiers.familiarity
    points = ruleset.modifiers.ranges[Modifier.FAMILIARITY]
    reading = reading_for(searcher.tags, ruleset.tags)
    arm = {
        FamiliarityReading.REPETITION: float(points.maximum),
        FamiliarityReading.VARIETY: float(points.minimum),
        FamiliarityReading.NEITHER: points.minimum * rules.default_lean,
    }[reading]
    return ModifierPoints(
        modifier=Modifier.FAMILIARITY,
        points=arm * strength_of(facts.shared_history, ruleset),
    )


def strength_of(history: SharedHistory, ruleset: Ruleset) -> float:
    """``0.5 ^ (days / half_life) × (1 − φⁿ)`` — decay by time, depth by count.

    Named rather than inlined because the two halves answer different questions
    and only together say *how familiar are these two, now*: an eight-month-old
    single game sits at 15% of full, which is §9.4's *effectively fresh again*
    without pretending it never happened.

    ``depth_phi`` carries the tag curve's value and is a **separate constant with
    its own falsifier** — a coincidence of values must never become a shared
    constant, so this reads the familiarity rules and never ``TagRules.phi``.
    """

    rules = ruleset.modifiers.familiarity
    decay: float = 0.5 ** (history.days_since_last_game / rules.half_life_days)
    depth: float = 1.0 - rules.depth_phi**history.games_played_together
    return decay * depth


def reading_for(tags: tuple[str, ...], rules: TagRules) -> FamiliarityReading:
    """Which way familiarity points for a searcher holding these tags.

    Read from the **searcher's** own declared tags and never the candidate's,
    over a second and separate map from the relationship matrix. **This is not a
    double-count against the tag terms**, which read the same ids: the tag does
    not add points through familiarity, it selects which direction familiarity
    points, and a selector is not an addend.

    **Repetition wins a tie**, so a player who says both *I want a regular game*
    and *I want to meet people* is read as wanting the regular game — the claim
    that is specific about *who*. A tag outside the map is not read at all: the
    map is exhaustive over ``WHY_YOU_ARE_HERE`` and a tag about the hour on court
    says nothing about repetition.
    """

    readings = {
        rules.familiarity_reading_map[tag]
        for tag in tags
        if tag in rules.familiarity_reading_map
    }
    if FamiliarityReading.REPETITION in readings:
        return FamiliarityReading.REPETITION
    if FamiliarityReading.VARIETY in readings:
        return FamiliarityReading.VARIETY
    return FamiliarityReading.NEITHER


def absorbed(appearances: int | None, rules: ModifierRules) -> bool:
    """Whether the engine has volunteered this player to newcomers often enough.

    ``NEWCOMER_ABSORPTION_CAP`` bounds **the ask** and never the person
    (``docs/adr/0114``): past it, the welcoming modifier and the newcomer-driven
    reorder are dropped and the player still ranks on their merits. Nobody is
    withheld, nobody is told, and there is no shape here that could withhold
    anybody — this answers a question about a *lift*, and the gate roster is
    somewhere else entirely.

    **Two of the three ways this is false are the day-one ones**, and both are
    spelled apart rather than collapsed into one falsy test. ``appearances is
    None`` is *this search is not a newcomer's*, so there is nothing to bound; a
    ``None`` cap is *the constant keeps its rule and refuses its integer*
    (``the-engine.md`` §6), so the tally is counted and carried and no comparison
    against it can be true. **Wired, and never binding.**

    At the cap and not past it, because the cap is *how often* — the appearance
    that reaches it is the last one the engine volunteers them for.

    **It bounds the welcoming record and nothing else** — the one place it is
    called. ``docs/adr/0114`` §3 named two things to drop, and the two turn out
    to reach opposite people: the welcoming record is an experienced player's,
    while the newcomer lift fires only for a candidate who is *themselves*
    inside the window. Capping both made the cap take its subsidy from the very
    population it exists to keep from being leaned on, so the ADR is amended and
    the lift is left alone. What remains is the sentence the ADR argues for
    throughout: *newcomers are matched by the strongest, most reliable half of
    the pool, because those are the players ``welcoming_record`` and the
    tightened gate select* — and this is the bound on how often the engine
    volunteers one of them.
    """

    cap = rules.newcomer_absorption_cap
    if cap is None or appearances is None:
        return False
    return appearances >= cap


def welcoming_record(facts: ModifierFacts, ruleset: Ruleset) -> ModifierOutcome:
    """Whether the candidate has played opponents whose rating was still settling.

    **One input, and unpaid** (#175). The prototype's version read sportsmanship,
    opponent variety and a history of wide-band opponents together — and the
    first two are already paid for by the reliability term and by a strand that
    was withdrawn, so a modifier reading them would charge the same facts twice.
    What is left is the one fact nothing else weighs.

    ``None`` from the provider is **no answer** rather than *no*: the record
    lives in ``matches``, which does not exist, and a false here would claim the
    platform had looked. The two are spelled apart below even though they reach
    the same outcome today — collapsing them into one falsy test is how *we have
    not asked* silently becomes *we asked and they have not*, and the day the
    provider lands is the day the difference starts costing somebody points.

    **Past the absorption cap it is dropped rather than reduced.** The record is
    still true; what has changed is that the engine stops paying for it, which is
    the whole of what *bounding the ask* means — the player keeps every point the
    eight terms gave them.
    """

    if facts.welcomed_settling_opponents is None:
        return None
    if not facts.welcomed_settling_opponents:
        return None
    if absorbed(facts.newcomer_appearances, ruleset.modifiers):
        return None
    return ModifierPoints(
        modifier=Modifier.WELCOMING_RECORD,
        points=float(ruleset.modifiers.ranges[Modifier.WELCOMING_RECORD].maximum),
    )


def reliability_floor_breach(
    candidate: ScorableCandidate, ruleset: Ruleset
) -> ModifierOutcome:
    """The dock for a **published** Player Score under the bar.

    **This is the one deliberate place the matcher reads the blend** rather than
    the six strands, and it is recorded as an exception so it never later reads
    as an oversight: a penalty justified by a figure that exists nowhere a human
    can look is unexplainable, and a player who works their visible score back up
    must be able to watch the penalty lift.

    **A dock, not an exclusion.** Refusing to show a genuinely good match over one
    missed game is the block's job and not the matcher's — which is also why the
    penalty is derived from the budget rather than picked: it is the smallest
    number that keeps a stack of small positives from erasing a no-show.

    A candidate with no record at all takes no dock. There is nothing to read,
    and an absent Player Score is not a low one.
    """

    record = candidate.reliability
    if (
        record is None
        or record.published_score >= ruleset.reliability.published_score_bar
    ):
        return None
    return ModifierPoints(
        modifier=Modifier.RELIABILITY_FLOOR_BREACH,
        points=float(ruleset.modifiers.floor_breach_penalty),
    )


def modify(
    searcher: Searcher,
    candidate: ScorableCandidate,
    facts: ModifierFacts,
    ruleset: Ruleset,
) -> ModifierStack:
    """Every modifier's outcome, **in ``BUDGETED_MODIFIERS``' own order**.

    One place the three are called, so *which modifiers exist* is a fact about
    the roster rather than about whoever last edited a pipeline — and the two
    ways this could go wrong silently are checked rather than trusted, exactly as
    they are for the terms: a modifier missing from the list would leave the
    budget holding less than it claims, and a modifier answering out of position
    would print under its neighbour's name.

    The dock is assembled beside the three and never inside them, because it is
    outside the budget and a tuple somebody sums is how it would quietly get in.
    """

    outcomes: tuple[ModifierOutcome, ...] = (
        calibration_value(searcher, facts, ruleset),
        familiarity(searcher, facts, ruleset),
        welcoming_record(facts, ruleset),
    )
    invariant(
        len(outcomes) == len(BUDGETED_MODIFIERS),
        f"a budgeted modifier is never read: {len(outcomes)} of "
        f"{len(BUDGETED_MODIFIERS)}",
    )
    for modifier, outcome in zip(BUDGETED_MODIFIERS, outcomes, strict=True):
        invariant(
            outcome is None or outcome.modifier is modifier,
            f"the outcome in {modifier.value}'s position answers for "
            f"{outcome.modifier.value if outcome else None}",
        )
    return ModifierStack(
        fired=tuple(outcome for outcome in outcomes if outcome is not None),
        floor_breach=reliability_floor_breach(candidate, ruleset),
        rules=ruleset.modifiers,
    )
