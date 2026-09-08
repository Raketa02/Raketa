"""The eight terms of Fit, each one number in ``[0, 1]`` — or a stand-down.

**Every term returns a value with structured evidence, or stands down**, in which
case it is dropped from the sum and the surviving weights renormalise
(``fit.py``). ``NoEvidence`` is never ``0`` and never a neutral ``0.5``, and that
single rule is why a 78 built on four facts is distinguishable from a 78 built on
seven.

**A stand-down names whose gap it is**, because *reliability is not a thing here
yet* and *they have not said what kind of evening they want* are two different
sentences and arrived as one flat list. A term function may author exactly the
two person-side codes: it knows which side was empty and cannot know whether a
provider exists at all, which is decided one layer out in ``floor.py``.

The distinction the whole file turns on: **a zero is a measurement and a
stand-down is not**. Two grids read with nothing in common is a fact about the
pair and scores zero; a grid nobody has ticked is not a fact about anybody and
scores nothing at all. Every term below is written so that the two cases cannot
be reached by the same branch.

**No constants live here.** Every number these functions read comes off the
ruleset, because changing one must be a dated release rather than a code change
(``docs/adr/0093``). The exceptions are arithmetic identities — ``1``, the ends
of ``[0, 1]`` — which are not numbers anybody can release.

**Nothing here reads a protected characteristic**, and that is true because the
value is not in the process: ``ScorableCandidate`` has no field to read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.engines.matchfit.core import (
    DegradedReason,
    EvidenceKind,
    LevelDirection,
    ReliabilityStrand,
    SearchMode,
    Seat,
    TagColumn,
    TagRelationshipKind,
    Term,
)
from app.engines.matchfit.ruleset import (
    BalanceRules,
    DistanceRules,
    IntentRules,
    ModeRules,
    ReliabilityRules,
    Ruleset,
    TagRelationship,
    TagRules,
)
from app.engines.matchfit.evidence import (
    AvailabilityOverlapEvidence,
    DistanceEvidence,
    Evidence,
    IntentAlignmentEvidence,
    LevelFitEvidence,
    PlayingStyleEvidence,
    PredictedBalanceEvidence,
    ReliabilityEvidence,
    SharedSlot,
    SocialVibeEvidence,
    StrandReading,
    TagPair,
)
from app.engines.matchfit.scorable import (
    GridCell,
    RatioObservation,
    RATING_CEILING,
    RATING_FLOOR,
    ScorableCandidate,
    Searcher,
    StrandObservation,
)
from app.engines.matchfit.scoring import StoodDown
from app.kernel import invariant


@final
@dataclass(frozen=True, slots=True)
class TermReading:
    """One term's answer: a number in ``[0, 1]`` and the evidence behind it.

    **A term may not emit evidence of another term's kind.** The check is here
    rather than in a review because the mistake is invisible on the wire: the
    breakdown still adds up, and one card silently explains its availability
    under the heading of its level.
    """

    term: Term
    value: float
    evidence: Evidence

    def __post_init__(self) -> None:
        invariant(
            0.0 <= self.value <= 1.0,
            f"{self.term.value} read {self.value}, which is outside [0, 1]",
        )
        invariant(
            self.evidence.kind is self.term.evidence_kind,
            f"{self.term.value} emitted {self.evidence.kind.value} evidence rather "
            f"than {self.term.evidence_kind.value}",
        )


#: A term either produced a reading or **stood down**, and there is no third
#: value. It is spelled as a type rather than as ``None`` for two reasons: there
#: is no number that means it — not ``0``, which is a measurement, and not
#: ``0.5``, which is an invented one — and a bare ``None`` made *this term stood
#: down* and *nobody wrote this term* the same value, on a tuple whose whole job
#: is to be read positionally.
TermOutcome = TermReading | StoodDown


def level_fit(
    searcher: Searcher, candidate: ScorableCandidate, rules: ModeRules
) -> TermOutcome:
    """How close the two Levels are, on the mode's own curve.

    **Two curves, and the difference is a claim about the game.** Competitive
    prices every tenth of a point from zero. For fun opens with a free band
    inside which a gap costs nothing at all, on the claim that *a friendly
    against someone a quarter-point above you is no worse than one against your
    exact twin*.

    **The tolerance is absolute on μ and this term never calls ``band_for``.**
    The shipped bands are deliberately uneven because *evidence* is unevenly
    available down the scale, not because a tenth of a point means less at the
    top — so a band-relative tolerance would be reading a claim about proof as a
    claim about play. The same number is also the level gate, one per mode rather
    than two, so the gate and the curve can never drift apart.

    It never stands down: a candidate without a Level is not in the index.
    """

    delta = abs(candidate.level.mu - searcher.level.mu)
    if rules.free_band is None:
        value = clamp_unit(1.0 - delta / rules.level_tolerance)
    else:
        # `None` is *the concept does not apply here* rather than a width of
        # zero, so the two curves are written as two rather than folded into one
        # that reads a null as a number.
        priced = max(0.0, delta - rules.free_band)
        value = clamp_unit(1.0 - priced / (rules.level_tolerance - rules.free_band))
    return TermReading(
        term=Term.LEVEL_FIT,
        value=value,
        evidence=LevelFitEvidence(
            my_mu=searcher.level.mu,
            their_mu=candidate.level.mu,
            delta=delta,
            direction=_direction(searcher.level.mu, candidate.level.mu),
        ),
    )


def predicted_balance(
    searcher: Searcher, candidate: ScorableCandidate, rules: BalanceRules
) -> TermOutcome:
    """How even the game is forecast to be, normalised across its own clamp.

    **The clamp bounds are the term's zero and one, not cosmetics.** Normalising
    over ``[0, 100]`` instead would waste the bottom third of the range on
    forecasts the model never produces, which is the defect this fix is the
    second instance of.

    The forecast goes blind at a Δμ of roughly a third of a point for a typical
    combined σ — that is where ``pct`` reaches its floor and stops
    discriminating, and it is exactly what the level gate exists to cover.

    **The most directly falsifiable numbers in the engine**: a forecast is
    checkable against confirmed results, where a weight is only checkable against
    behaviour.
    """

    pct = forecast_pct(
        abs(candidate.level.mu - searcher.level.mu), candidate.combined.sigma, rules
    )
    return TermReading(
        term=Term.PREDICTED_BALANCE,
        value=balance_norm(pct, rules),
        evidence=PredictedBalanceEvidence(
            # The printed forecast is a whole percent; the term's own reading is
            # not rounded, because rounding a value that is about to be weighed
            # by 19.5 would move the Fit by a fifth of a point for nothing.
            pct=int(round(pct)),
            my_sigma=searcher.level.sigma,
            their_sigma=candidate.level.sigma,
            confidence=candidate.combined.confidence,
        ),
    )


def forecast_pct(gap: float, sigma: float, rules: BalanceRules) -> float:
    """``clamp(100 − gap·mu_coefficient − σ·sigma_coefficient, min, max)``.

    **One forecast, two sets of people.** A pairing's gap is between two players
    and a four's is between two side strengths, but the claim being made — *how
    even will this be* — is the same claim and reads the same three numbers. The
    group objective calls this rather than carrying a second copy, which is the
    same rule the two tag columns follow one function down.

    Unrounded: the term weighs this and the card prints a whole percent of it,
    and rounding a value about to be multiplied by a weight would move the answer
    for nothing.
    """

    return min(
        float(rules.pct_max),
        max(
            float(rules.pct_min),
            100.0 - gap * rules.mu_coefficient - sigma * rules.sigma_coefficient,
        ),
    )


def balance_norm(pct: float, rules: BalanceRules) -> float:
    """A forecast as a reading in ``[0, 1]``, **across its own clamp**.

    The clamp bounds are the term's zero and one, not cosmetics. Normalising over
    ``[0, 100]`` instead would waste the bottom third of the range on forecasts
    the model never produces, which is the defect this is the second instance of.
    """

    return (pct - rules.pct_min) / (rules.pct_max - rules.pct_min)


def intent_alignment(
    searcher: Searcher, candidate: ScorableCandidate, rules: IntentRules
) -> TermOutcome:
    """What kind of evening each of them is after — one of six cells.

    **Not declaring is not a cell.** It stands the term down and renormalises it
    away, which is what makes declaring *against* the searcher cost strictly more
    than silence: the opposite declaration reads the table's zero and loses the
    term's whole weight, where silence loses nothing and redistributes it.

    **Intent is a weight and never a gate**, and the zero is the whole charge. A
    second dock on top of it would be a gate wearing a modifier's clothes.
    """

    declaration = candidate.declared_intent
    if declaration is None:
        return StoodDown(
            term=Term.INTENT_ALIGNMENT, reason=DegradedReason.NOTHING_FROM_THEM
        )
    # The value form of `invariant`: it narrows away the `None`, so a cell that
    # is priced at 0.00 — the directly opposite declaration — passes through
    # while an *unpriced* declaration raises. A bare truth test would confuse
    # those two, and the second is the one this ruleset cannot answer.
    value = invariant(
        rules.alignment[searcher.mode].get(declaration),
        f"a candidate declared {declaration!r}, which this ruleset does not "
        f"price in {searcher.mode.value}",
    )
    return TermReading(
        term=Term.INTENT_ALIGNMENT,
        value=value,
        evidence=IntentAlignmentEvidence(
            my_mode=searcher.mode,
            their_intent=declaration,
            aligned=declaration == rules.same_evening[searcher.mode],
        ),
    )


def reliability(
    candidate: ScorableCandidate, mode: ModeRules, rules: ReliabilityRules
) -> TermOutcome:
    """What the record says about turning up — six strands, read separately.

    **The six are never blended into one number before they get here.** The two
    mode vectors order people oppositely — a candidate strong on *answers about
    results* and weak on *sportsmanship* wins a counted game and loses a
    friendly — and a single blended score cannot express that. The decomposition
    is justified for exactly as long as such a pair exists.

    **Two standing-down powers, and they bind at different scopes.** A strand
    below **its own** observation bar stands down **alone** and the survivors
    renormalise inside the term, because one no-show out of one game is not
    thirty-five out of thirty-eight — and the bar is per strand rather than one
    number over all of them, so a strand that needs more evidence than the rest
    can ask for it without moving what the platform demands of a newcomer
    (``docs/adr/0156``). If the most recent observation across the whole record
    is past the horizon, the **term** stands down: the strands share one cause —
    *this player stopped playing* — so an old record is old all the way through.

    **The matcher applies no decay of its own.** The score is a memory and fades
    with new evidence on the provider's side; a second decay here would
    double-count. Standing a strand down is the entire policy.
    """

    record = candidate.reliability
    if record is None:
        return _no_record()
    if record.days_since_last_observation > rules.horizon_days:
        return _no_record()

    readings: list[StrandReading] = []
    weighted = 0.0
    basis = 0
    # The six in their own declaration order, never over the mapping's, so the
    # evidence reads the same way whatever order a provider filled it in.
    for strand in ReliabilityStrand:
        observation = record.strands.get(strand)
        if observation is None:
            continue
        if observation.observations < rules.min_observations[strand]:
            continue
        value = _strand_value(observation)
        readings.append(StrandReading(strand=strand, value=value))
        weight = mode.strand_weights[strand]
        weighted += weight * value
        basis += weight
    if not readings or basis == 0:
        # Nothing survived, or everything that did carries no weight in this
        # mode. Either way there is no reading — and a term with no reading
        # stands down rather than reporting the zero it did not measure.
        return _no_record()

    return TermReading(
        term=Term.RELIABILITY,
        value=weighted / basis,
        evidence=ReliabilityEvidence(
            # The **published** Player Score, never the per-mode blend above. A
            # penalty justified by a figure that exists nowhere a human can look
            # is unexplainable, and a player who works their visible score back
            # up must be able to watch the penalty lift.
            score=record.published_score,
            strands=tuple(readings),
            floor_breached=record.published_score < rules.published_score_bar,
        ),
    )


def availability_overlap(
    searcher: Searcher, candidate: ScorableCandidate
) -> TermOutcome:
    """``|shared| / |mine|`` — the glossary's ratio, and **no constants at all**.

    The denominator is the **searcher's** ticked cells, because the question it
    answers is *how much of my week does this person cover*. That is what makes
    the reading asymmetric and a fact about the pair rather than about either
    person; the reverse direction flips the denominator and nothing else.

    **A blank grid on either side stands the term down**, and that clause is
    load-bearing twice: it is the only thing between this term and a division by
    zero, and scoring a cleared grid as ``0`` would be an invented zero — *blank
    means we do not know*, which is not the same claim as *you two never
    overlap*.

    Significance, staleness and proximity are all struck and none of them
    returns as a hidden constant here: none of the three reads the pair.
    Proximity keeps its two honest jobs — it orders the times rung's offers, and
    it names the next shared cell below, which is evidence a game can be
    *arranged* and never a proposed time.
    """

    if not searcher.grid:
        # **The searcher's blank grid wins the tie**, and the branch order is
        # where that is said. Both grids blank is one sentence to write and it is
        # the one the reader can act on.
        return StoodDown(
            term=Term.AVAILABILITY_OVERLAP, reason=DegradedReason.NOTHING_FROM_YOU
        )
    if not candidate.grid:
        return StoodDown(
            term=Term.AVAILABILITY_OVERLAP, reason=DegradedReason.NOTHING_FROM_THEM
        )
    theirs = frozenset(candidate.grid)
    shared = tuple(cell for cell in searcher.grid if cell in theirs)
    return TermReading(
        term=Term.AVAILABILITY_OVERLAP,
        value=len(shared) / len(searcher.grid),
        evidence=AvailabilityOverlapEvidence(
            shared_count=len(shared),
            next_slot=_next_shared(shared, searcher),
        ),
    )


def playing_style(
    searcher: Searcher, candidate: ScorableCandidate, seat: Seat, rules: TagRules
) -> TermOutcome:
    """What the two of them are like during the hour on court."""

    return _tag_term(
        TagColumn.STYLE,
        Term.PLAYING_STYLE,
        PlayingStyleEvidence,
        searcher,
        candidate,
        seat,
        rules,
    )


def social_vibe(
    searcher: Searcher, candidate: ScorableCandidate, seat: Seat, rules: TagRules
) -> TermOutcome:
    """What the two of them are like around the game."""

    return _tag_term(
        TagColumn.VIBE,
        Term.SOCIAL_VIBE,
        SocialVibeEvidence,
        searcher,
        candidate,
        seat,
        rules,
    )


def distance(
    searcher: Searcher, candidate: ScorableCandidate, rules: DistanceRules
) -> TermOutcome:
    """How far, as a fraction of **the searcher's own** ring.

    Full marks inside the shoulder, zero past the ring. Both ends are fractions
    of the radius the searcher set for themselves, so a ten kilometre searcher
    and a fifty kilometre one are each read against what they said far means.

    **The candidate's own radius is printed and never scored.** Somebody who set
    a small ring is not refusing to be found, so the searcher sitting outside it
    is a Liveness dock and never a gate — and the standalone flat dock for it is
    struck, because the reciprocal reading already prices it proportionately.
    """

    span = (rules.zero_at - rules.full_marks_within) * searcher.radius_km
    value = clamp_unit(
        (rules.zero_at * searcher.radius_km - candidate.distance_km) / span
    )
    return TermReading(
        term=Term.DISTANCE,
        value=value,
        evidence=DistanceEvidence(
            km=int(round(candidate.distance_km)),
            area_code=candidate.area_code,
            outside_their_radius=candidate.distance_km > candidate.radius_km,
        ),
    )


def read_terms(
    searcher: Searcher,
    candidate: ScorableCandidate,
    ruleset: Ruleset,
    seat: Seat,
) -> tuple[TermOutcome, ...]:
    """Every term's outcome, **in ``Term``'s own order**.

    One place the eight are called, so *which terms exist* is a fact about the
    enum rather than about whoever last edited a pipeline. Two ways this could go
    wrong are checked rather than trusted, because both are silent: a term
    missing from the list would renormalise its weight onto the others and the
    Fit would still add up, and a term answering out of position would be weighed
    at its neighbour's weight — a wrong number that looks like a plausible one.

    **The position check now covers a stand-down too**, which the bare ``None``
    it replaced could not be asked: a term that stood down names itself, so the
    one outcome that used to pass this unexamined is the one the degraded list is
    read positionally against.
    """

    mode = ruleset.modes[searcher.mode]
    readings: tuple[TermOutcome, ...] = (
        level_fit(searcher, candidate, mode),
        predicted_balance(searcher, candidate, ruleset.balance),
        intent_alignment(searcher, candidate, ruleset.intent),
        reliability(candidate, mode, ruleset.reliability),
        availability_overlap(searcher, candidate),
        playing_style(searcher, candidate, seat, ruleset.tags),
        distance(searcher, candidate, ruleset.distance),
        social_vibe(searcher, candidate, seat, ruleset.tags),
    )
    invariant(
        len(readings) == len(Term),
        f"a term of Fit is never read: {len(readings)} of {len(Term)}",
    )
    for term, reading in zip(Term, readings, strict=True):
        invariant(
            reading.term is term,
            f"the reading in {term.value}'s position answers for "
            f"{reading.term.value}",
        )
    return readings


# ---------------------------------------------------------------------------
# The tag arithmetic, shared by the two columns — and by the group objective,
# which reads the same rows about two people neither of whom is the searcher
# ---------------------------------------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class TagColumnReading:
    """One column's reading over **two people**, whoever they are.

    Fit calls it about the searcher and a candidate and prints it as a term; the
    group objective calls it about two candidates and feeds it to a cross
    reading. Neither is a special case of the other, so what they share is this
    shape and the arithmetic that produces it — *how do these two get on* has one
    implementation, called six times in a four, three printed and three scored.

    It carries the lists as well as the number because the printing caller needs
    them and the scoring one does not, and a reading that answered only the
    scorer would be a second, quieter version of the same computation.
    """

    value: float
    matched: tuple[str, ...]
    complementary: tuple[TagPair, ...]
    clashing: tuple[TagPair, ...]


def tag_column(
    column: TagColumn,
    mine: tuple[str, ...],
    theirs: tuple[str, ...],
    mode: SearchMode,
    seat: Seat,
    rules: TagRules,
) -> TagColumnReading | DegradedReason:
    """One tag column: ``dr(matches) + complements − clashes``, renormalised.

    **The split between the two terms is by relationship, not by tag group.**
    Every matrix row carries its own column, so one id can be read for the hour
    on court in one row and for the evening around it in another — which the
    group split cannot do, and its own pair table is the proof: five of the
    eleven relationships it lists cross the boundary it draws.

    **The term's zero is a real clash and not an absence of relationship.**
    Normalising over ``[−cap, 1]`` rather than clamping at zero is what makes the
    clash arm visible at all: scored the other way, *"you two clash badly"* is
    numerically identical to *"you two share nothing"* — and two random four-tag
    draws from nineteen overlap under once on average, so the *typical* pair
    would sit at the bottom of a term carrying a quarter of a friendly. Nothing
    firing reads the **measured** zero instead: *different, not incompatible*.

    **A column stands down when either side holds no tag in its domain**, and the
    domain is derived from the matrix rather than declared, so it re-derives
    itself the moment product edits a row. That is the difference between *they
    said nothing about the hour on court* and *we looked and nothing fired* — and
    a tag about the **person** rather than the game takes no row at all, so it is
    in no domain, and it may be shown and may never score.

    **Which side was empty comes back, and the code is positional**: it names
    ``mine`` or ``theirs``, which for a term of Fit are the searcher and the
    candidate. A cross reading takes the value and drops the code, because in a
    four neither of the two people is *you* — and one implementation of the
    domain check is worth more than a vocabulary that reads perfectly at both
    call sites and is written twice.

    **Where no seat is assigned the pair reads the ``OPPONENT`` row**, so a
    ``PARTNER``-only row does not fire on an unseated shortlist: the harsher
    reading applies only once somebody is being seated as a partner, because
    being wrong about a clash buries a person.

    **The mode is the search's and never a person's.** A cross pair sits inside
    one search, so both readings of it run under the vector the searcher chose;
    a row scoped to the other mode does not fire for anybody in that four.
    """

    domain = rules.column_domain(column)
    if not any(tag in domain for tag in mine):
        # The searcher's own silence wins the tie, for the reason a blank grid
        # does: it is the only one of the two the reader can act on.
        return DegradedReason.NOTHING_FROM_YOU
    if not any(tag in domain for tag in theirs):
        return DegradedReason.NOTHING_FROM_THEM

    held = frozenset(mine)
    other = frozenset(theirs)
    matched: list[str] = []
    complements: list[float] = []
    complementary: list[TagPair] = []
    clashing: list[TagPair] = []
    severity_total = 0.0
    # Rows in the matrix's own order, so the evidence lists read the same way on
    # every process and every run (`docs/adr/0105`).
    for row in rules.relationship_matrix:
        if row.column is not column or mode not in row.modes:
            continue
        if seat not in row.seats or not _fires(row, held, other):
            continue
        if row.kind is TagRelationshipKind.MATCH:
            matched.append(row.a)
        elif row.kind is TagRelationshipKind.COMPLEMENT:
            complements.append(
                row.strength if row.strength is not None else rules.complement_strength
            )
            complementary.append(TagPair(a=row.a, b=row.b))
        else:
            severity = invariant(
                row.severity, f"a clash row with no severity: {row.pair}"
            )
            severity_total += rules.clash_severities[severity]
            clashing.append(TagPair(a=row.a, b=row.b))

    raw = (
        diminishing(len(matched), rules.phi)
        + diminishing_at_strengths(complements, rules.phi)
        - min(severity_total, rules.clash_cap)
    )
    return TagColumnReading(
        value=clamp_unit((raw + rules.clash_cap) / (1.0 + rules.clash_cap)),
        matched=tuple(matched),
        complementary=tuple(complementary),
        clashing=tuple(clashing),
    )


def _tag_term(
    column: TagColumn,
    term: Term,
    variant: type[PlayingStyleEvidence] | type[SocialVibeEvidence],
    searcher: Searcher,
    candidate: ScorableCandidate,
    seat: Seat,
    rules: TagRules,
) -> TermOutcome:
    """One column, as a **term of Fit** — the reading above, printed.

    The variant is handed in rather than re-derived from the term: the two
    callers already know which of the two shapes they are, and branching on the
    term here would be a second place that mapping could go wrong.
    """

    reading = tag_column(
        column, searcher.tags, candidate.tags, searcher.mode, seat, rules
    )
    if isinstance(reading, DegradedReason):
        return StoodDown(term=term, reason=reading)
    return TermReading(
        term=term,
        value=reading.value,
        evidence=variant(
            matched=reading.matched,
            complementary=reading.complementary,
            clashing=reading.clashing,
        ),
    )


def _fires(row: TagRelationship, mine: frozenset[str], theirs: frozenset[str]) -> bool:
    """``(a∈S ∧ b∈C) ∨ (b∈S ∧ a∈C)`` — at most once per row, whoever holds what.

    A shared tag may pay both a match and a complement. They are two different
    claims — *you both want this* against *your two things fit together* — and
    refusing the second would delete the complement rows for exactly the pairs
    they describe best.
    """

    return (row.a in mine and row.b in theirs) or (row.b in mine and row.a in theirs)


def diminishing(count: int, phi: float) -> float:
    """``dr(n) = 1 − φⁿ``. The second matched tag is worth less than the first.

    Tag-stuffing therefore does not pay — and the platform caps selection at six
    precisely because it expects people to try.
    """

    return 1.0 - phi**count


def diminishing_at_strengths(strengths: list[float], phi: float) -> float:
    """The complement arm, where the rows do **not** all carry one strength.

    ``strength · dr(n)`` is written for a single discount, and the shipped matrix
    has rows at parity beside rows at the default — so *which* complement takes
    the first, largest increment is a question the one-strength form cannot ask.

    ``dr`` is a sum of shrinking increments, ``Σ (1 − φ)·φ ⁱ``, so the arm is
    that sum with each increment priced at one row's own strength. **Strongest
    first**, which is what makes adding a row never subtract from the total: pair
    a weaker claim with a larger increment and a second complement could lower
    the score. It reduces to ``strength · dr(n)`` exactly when every row carries
    the same strength, which is the form the constant table names.
    """

    total = 0.0
    for position, strength in enumerate(sorted(strengths, reverse=True)):
        total += strength * (1.0 - phi) * phi**position
    return total


# ---------------------------------------------------------------------------
# Small shared arithmetic
# ---------------------------------------------------------------------------


def clamp_unit(value: float) -> float:
    """Hold a reading inside ``[0, 1]``, the range every term shares.

    Public because the group terms share the range as well as the rule: a second
    copy one directory over would be the same one-liner with its own chance of
    being wrong at an end.
    """

    return max(0.0, min(1.0, value))


def _direction(mine: float, theirs: float) -> LevelDirection:
    """Which side of the searcher the candidate sits on.

    A code rather than a sign on ``delta``, because the client's sentence differs
    in all three cases. Equality is exact: Levels are carried to two decimals, so
    *the same Level* is a comparison and not a tolerance.
    """

    if theirs == mine:
        return LevelDirection.LEVEL
    return LevelDirection.ABOVE if theirs > mine else LevelDirection.BELOW


def _no_record() -> StoodDown:
    """Reliability's stand-down — **one code for all three of its causes**.

    No record at all, a record whose most recent observation is past the horizon,
    and a record on which no strand cleared the observation bar are three
    different facts here and **one sentence outside**. Distinguishing them on the
    wire would publish activity recency, which ``docs/adr/0106`` §5 refuses by
    name, so the three causes are collapsed at the only point where all three are
    visible rather than trusted not to be separated later.
    """

    return StoodDown(term=Term.RELIABILITY, reason=DegradedReason.NOTHING_FROM_THEM)


def _strand_value(observation: StrandObservation) -> float:
    """One strand as a reading in ``[0, 1]``.

    A ratio strand publishes the figure the player is shown and it is **read, not
    re-derived** — a card explaining a match with a number the player's own
    profile disagrees with is worse than one that says nothing.

    Sportsmanship publishes no such figure, so this is the one place the engine
    derives a strand: a mean over the rating scale's own ends, where the floor is
    the worst a player can be rated rather than an absence of ratings.
    """

    if isinstance(observation, RatioObservation):
        return observation.published_value / 100.0
    return (observation.mean - RATING_FLOOR) / (RATING_CEILING - RATING_FLOOR)


def _next_shared(shared: tuple[GridCell, ...], searcher: Searcher) -> SharedSlot | None:
    """The soonest cell both of them ticked, or ``None`` — a measured nothing.

    Day resolution, and the caller resolves *today* — no date, no timezone, the
    same signature the challenge window's derivation takes. A cell on today's
    weekday is nought days away whatever the hour is now, because the grid is a
    preference and not a promise, and the product's finest time precision is a
    third of a day.

    Ordering inside a day comes from ``Searcher.day_parts``: the engine is told
    where each part sits and never learns what one is called.
    """

    if not shared:
        return None
    soonest = min(
        shared,
        key=lambda cell: (
            (int(cell.day) - int(searcher.today)) % 7,
            searcher.day_parts.index(cell.part),
        ),
    )
    return SharedSlot(day=int(soonest.day), part=soonest.part)


#: Every evidence kind these terms can produce. Read by the tests that hold this
#: file and the wire union to one vocabulary — a term emitting a kind the union
#: does not publish renders as nothing at all on the one screen whose whole
#: promise is showing its working.
EMITTED_EVIDENCE_KINDS: frozenset[EvidenceKind] = frozenset(
    term.evidence_kind for term in Term
)

__all__ = [
    "EMITTED_EVIDENCE_KINDS",
    "TagColumnReading",
    "TermOutcome",
    "TermReading",
    "availability_overlap",
    "balance_norm",
    "clamp_unit",
    "diminishing",
    "diminishing_at_strengths",
    "distance",
    "forecast_pct",
    "intent_alignment",
    "level_fit",
    "playing_style",
    "predicted_balance",
    "read_terms",
    "reliability",
    "social_vibe",
    "tag_column",
]
