"""The group objective — the arithmetic that seats four people rather than one.

**A four contains six pairs, and the searcher is in three of them.** Every gate
and every term of Fit was decided while looking at a shortlist, where the
searcher is one half of every pair on the screen; the other three pairs are
invisible to Fit by construction. That is the whole reason ``G`` exists rather
than a sum of Fits, and it is the reason a player hand-picking three others is
doing this optimisation in their head, badly.

``docs/adr/0117`` sets the admissibility rule this file is written to:
**a term earns its place only by reading something no seat's Fit read.** Six
terms, and each one of them either reads a pair no Fit could see, or reads the
four at once::

    G = w_bal      · balance_norm(arrangement)
      + w_seatfit  · mean( post-modifier Fit of the unlocked non-viewer seats )
      + w_minfit   · min ( the same )
      + w_cross    · ( mean(cross reading over the three cross pairs) + seat_delta )
      + w_crossmin · min ( cross reading over the three cross pairs )
      + w_avail    · group_avail

**A cross reading invents no constant.** It is Fit's own person-to-person
sub-score — intent, playing style, social vibe — renormalised over its own three
terms through the same function Fit renormalises eight with, reading the same
matrix rows through the same seat scope. So *how do these two get on* has one
implementation, called six times in a four: three printed as Fit and three
scored here. The mode inversion arrives free with it — 51.7% of a for-fun Fit is
person-to-person against 31.0% competitive — so a cross reading is worth more in
a friendly without ``w_cross`` having to say so a second time.

**There is no group floor.** ``G`` is only ever compared to another ``G``:
nothing is seated because its objective cleared a bar, only because it beat
every other combination. It is recorded and never returned, and the evidence
half is paid by one closed reason code naming the term with the largest margin
between the winner and the runner-up.

**There is no ``G`` for singles, and the signature is where that is said.** With
two seats the mean and the min are the same number, there is no arrangement and
there are no cross pairs, so ``G`` reduces to a monotone transform of Fit plus a
re-charged balance term — a transform that is **not order-preserving**, so the
line-up route and the search route could name different best candidates for the
same search. Nothing here takes fewer than three seated people.

**``arrange()`` is not a separate step.** The seat delta and the cross pairs'
seat scopes both vary with the arrangement, so the combination is chosen by
``argmax G`` over all three pairings. *Even it out* keeps its own meaning — it
selects the min-gap arrangement — and the new fact the builder can state is that
the two differ, which happens precisely when a four's levels are near-equal and
balance has nothing left to say.
"""

from __future__ import annotations

from typing import Sequence

from app.engines.matchfit.core import (
    ForecastAssumption,
    GroupReason,
    GroupTerm,
    SearchMode,
    Seat,
    TagColumn,
    Term,
)
from app.engines.matchfit.grouping import (
    Arranged,
    Arrangement,
    Forecast,
    GroupScore,
    GroupTermReading,
    PersonalFacts,
    Seated,
    SigmaCombiner,
    Split,
)
from app.engines.matchfit.ruleset import (
    WEIGHT_TOTAL,
    BalanceRules,
    IntentRules,
    Ruleset,
)
from app.engines.matchfit.scorable import GridCell, LevelReading, Searcher
from app.engines.matchfit.v1.fit import renormalised_weights
from app.engines.matchfit.v1.liveness import reverse_mode
from app.engines.matchfit.v1.terms import (
    TagColumnReading,
    balance_norm,
    clamp_unit,
    forecast_pct,
    tag_column,
)
from app.kernel import invariant

#: The three terms of Fit a cross reading is made of — **the person-to-person
#: ones, and only those**. Level, balance, availability, distance and
#: reliability are facts about a pairing that the objective already reads at the
#: level of the four, or does not read at all because no court exists to
#: converge on. Declared here rather than derived, because *which three* is the
#: claim ``docs/adr/0117`` makes and a derivation would quietly re-decide it.
CROSS_TERMS = (Term.INTENT_ALIGNMENT, Term.PLAYING_STYLE, Term.SOCIAL_VIBE)

#: Where each group term sits, so a tie breaks on a declaration and never on a
#: dictionary's iteration order (``docs/adr/0105``).
_GROUP_ORDER = {term: position for position, term in enumerate(GroupTerm)}


# ---------------------------------------------------------------------------
# The cross reading, and the seat delta
# ---------------------------------------------------------------------------


def cross_reading(
    mode: SearchMode,
    mine: PersonalFacts,
    theirs: PersonalFacts,
    seat: Seat,
    ruleset: Ruleset,
) -> float | None:
    """How two people get on, in ``[0, 1]`` — **Fit's own sub-score, renormalised.**

    Three of Fit's eight terms are about the two people rather than about the
    game: what kind of evening each wants, what they are like during the hour on
    court, and what they are like around it. Renormalised over their own weights
    they are a reading of a pair that needs neither a new constant nor a second
    definition of anything — and because for fun puts more than half its weight
    on those three against competitive's third, the inversion the objective needs
    is already inside the number.

    **It stands down when all three do**, and the survivors renormalise when one
    or two do, exactly as Fit's do. Two candidates who have declared nothing and
    hold no tag in either column are not a cross pair reading zero; they are a
    cross pair nobody can read, and a zero would be the invented one this layer
    refuses everywhere else.

    **Symmetric, because a cross pair has no direction.** The matrix rows are
    already undirected, and the intent cell is read both ways round and taken at
    its worse — a pair's evening is only as shared as the less-satisfied half of
    it — so which of the two is named first cannot change the answer. Fit is
    asymmetric through familiarity and the availability denominator; neither of
    those is here, and neither should be, because there is no *mine* among two
    people who did not search.
    """

    weights = ruleset.modes[mode].weights
    readings = {
        Term.INTENT_ALIGNMENT: _cross_intent(mode, mine, theirs, ruleset.intent),
        Term.PLAYING_STYLE: _cross_tags(
            TagColumn.STYLE, mode, mine, theirs, seat, ruleset
        ),
        Term.SOCIAL_VIBE: _cross_tags(
            TagColumn.VIBE, mode, mine, theirs, seat, ruleset
        ),
    }
    live = tuple(term for term in CROSS_TERMS if readings[term] is not None)
    if not live:
        return None
    shares = renormalised_weights(weights, live)
    total = 0.0
    for term in live:
        # Narrowed by `live`, which was built from exactly this test — indexed
        # rather than re-tested so the two cannot come apart.
        reading = readings[term]
        assert reading is not None
        total += shares[term] * reading
    return total / WEIGHT_TOTAL


def seat_delta(searcher: Searcher, partner: Seated, ruleset: Ruleset) -> float:
    """What the searcher's own pair gains by being **seated** beside them.

    An unseated pair reads the forgiving ``OPPONENT`` rows and a ``PARTNER``-only
    row does not fire at all, because being wrong about a clash buries a person.
    The printed Fit therefore *deliberately declined* to take the partner
    reading, and this is where it is collected::

        seat_delta = cross_at(PARTNER, viewer, partner)
                   − cross_at(OPPONENT, viewer, partner)

    **Exactly zero for the two opponent seats, by construction** — there is no
    branch here that could forget it, because unseated already reads
    ``OPPONENT`` and this function is only ever asked about the partner pair.

    **It never re-scores a Fit.** The card said 78 in the shortlist and it says
    78 in the builder; the delta enters ``G`` and the line-up's reasons and
    nothing else. A Fit that moved when somebody crossed the net would be
    *Why 78?* failing on the one screen that promises to show its working
    (``docs/adr/0104``, ``docs/adr/0106``).

    Zero when the pair reads at neither seat: a delta between two absences is
    not a gain, and the intent component — which is what a pair with no tags is
    left with — is seat-blind and cancels itself.
    """

    mine = PersonalFacts.of_searcher(searcher, ruleset.intent)
    theirs = partner.personal
    seated = cross_reading(searcher.mode, mine, theirs, Seat.PARTNER, ruleset)
    unseated = cross_reading(searcher.mode, mine, theirs, Seat.OPPONENT, ruleset)
    if seated is None or unseated is None:
        return 0.0
    return seated - unseated


def _cross_intent(
    mode: SearchMode, mine: PersonalFacts, theirs: PersonalFacts, rules: IntentRules
) -> float | None:
    """Whether these two want the same evening — **read against each other.**

    Fit's intent term reads a candidate's declaration against the *searcher's
    mode*, which is a fact about that pairing and one the objective may not
    charge twice (``docs/adr/0117`` strikes ``group_intent_coherence`` for
    exactly that). A cross pair contains no searcher, so there is no mode to read
    against — and the table is keyed by one.

    So each declaration selects the vector it would be judged under, through
    ``reverse_mode`` and therefore through ``same_evening``: the same rule that
    decides which weights a reciprocal fit runs under, and the same reason
    ``NO_PREFERENCE`` selects nothing and inherits the search's mode instead.
    Each is then read against the other's declaration in the table that already
    prices six cells, **and the pair takes the worse of the two readings**.

    That is what makes an *opposed* cross pair zero in both modes rather than
    only in competitive, where the table's own zero sits: one direction of an
    opposed pair always reads a zero, and the minimum finds it. It is the whole
    of why ``w_crossmin`` earns its place on intent rather than on clashes.

    **Not declaring is not a cell**, here as in Fit: the component stands down
    and the other two renormalise, so silence still costs strictly less than
    declaring against somebody.
    """

    ours, yours = mine.declared_intent, theirs.declared_intent
    if ours is None or yours is None:
        return None
    return min(
        _alignment(mode, ours, yours, rules), _alignment(mode, yours, ours, rules)
    )


def _alignment(mode: SearchMode, reader: str, read: str, rules: IntentRules) -> float:
    """One direction of a cross pair's intent cell.

    The declarations are strings rather than the facts that carry them, because
    what selects a vector is *what somebody declared* and nothing else about
    them — and the value form of ``invariant`` keeps a cell priced at 0.00 apart
    from a declaration this ruleset cannot price at all.
    """

    vector = reverse_mode(mode, reader, rules)
    return invariant(
        rules.alignment[vector].get(read),
        f"a candidate declared {read!r}, which this ruleset does not price in "
        f"{vector.value}",
    )


def _cross_tags(
    column: TagColumn,
    mode: SearchMode,
    mine: PersonalFacts,
    theirs: PersonalFacts,
    seat: Seat,
    ruleset: Ruleset,
) -> float | None:
    """One tag column of a cross pair — the same rows Fit reads, at their seat."""

    reading = tag_column(column, mine.tags, theirs.tags, mode, seat, ruleset.tags)
    # The side code is dropped rather than translated: in a four neither of these
    # two people is the searcher, so *whose gap is this* has no answer a card
    # could print — and ``G`` renormalises over its own live terms, which is the
    # whole of what a stood-down column means here.
    return reading.value if isinstance(reading, TagColumnReading) else None


# ---------------------------------------------------------------------------
# The forecast, and the four-way intersection
# ---------------------------------------------------------------------------


def forecast(
    side_a: tuple[LevelReading, ...],
    side_b: tuple[LevelReading, ...],
    rules: BalanceRules,
    combine: SigmaCombiner,
    *,
    seats_per_side: int = 2,
) -> Forecast:
    """How even the game is forecast to be, for two sides of one or two people.

    **One implementation produces the arranged figure and the provisional one**,
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
    engine. The coefficients and the clamp are the pairwise term's own: a
    forecast about four people is the same claim as a forecast about two, made
    over two side strengths instead of two players.
    """

    pct, sigma, _ = _predicted(side_a, side_b, rules, combine, seats_per_side)
    return _forecast(
        pct,
        sigma,
        partial=len(side_a) < seats_per_side or len(side_b) < seats_per_side,
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


def group_availability(grids: Sequence[tuple[GridCell, ...]]) -> float | None:
    """``|shared₄| / min over the four of |their declared slots|``. **No constants.**

    Three good pairwise overlaps do not imply a four-way one: a searcher free
    Monday and Tuesday, one candidate free Monday, one free Tuesday and one free
    Monday reads well on every Fit and gives **a four with no common slot**. This
    is the only term that can see that, which is exactly what admits it.

    The denominator is the **smallest** declared grid, because among four people
    there is no *mine* for the pairwise term's asymmetry to point at — so the
    group's coverage is measured against the person with least to give. It is
    the pairwise term's ``significance`` surviving where its own argument against
    it does not apply: there, it duplicates ``overlap``; here, there is no
    ``overlap`` for it to duplicate.

    **A term and not a gate.** An empty intersection zeroes it — sixteen points
    of a competitive objective and twenty of a friendly — and the screen says
    *you would all have to bend*; it never removes the four. The pairwise term
    does not gate at zero either, and the times rung relaxes exactly these slots.

    **A blank grid stands it down**, as it stands the pairwise term down: it is
    the only thing between this term and a division by zero, and *blank means we
    do not know* is a different claim from *you four never overlap*.
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

    Unrounded because the objective weighs this and the card prints it, and
    rounding a value about to be multiplied by 34 would move ``G`` for nothing —
    the same division ``predicted_balance`` makes between its reading and its
    evidence. **The split comes back beside them rather than being re-derived by
    whoever wants it**, because *Even it out* selects on exactly the distance
    this forecast was computed from and the card prints exactly the two
    strengths that distance is between: four numbers, one computation, and no
    second subtraction anywhere for them to disagree in.

    ``side_a`` is the searcher's own side wherever an arrangement is being read,
    and that is what fixes the split's orientation — there is no arrangement in
    which the searcher crosses the net.
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
    three arrangements of one four three different games. At parity every
    arrangement of the same people would forecast identically and the seat delta
    would be deciding alone.
    """

    stronger = max(level.mu for level in side)
    weaker = min(level.mu for level in side)
    share = rules.stronger_partner_share
    return share * stronger + (1.0 - share) * weaker


# ---------------------------------------------------------------------------
# The objective, and the three arrangements
# ---------------------------------------------------------------------------


def objective(
    searcher: Searcher,
    arrangement: Arrangement,
    ruleset: Ruleset,
    combine: SigmaCombiner,
) -> GroupScore:
    """``G`` for one arrangement of one four, over exactly the six terms.

    A term that cannot be read stands down and the survivors renormalise, exactly
    as Fit's eight do — so ``G`` stays a number out of a hundred whatever the four
    could be read on, and ``degraded_terms`` travels beside it because two
    objectives computed on different bases are otherwise not comparable a year
    later.

    ``mean`` and ``min`` read the **unlocked** seats only. A seat the searcher
    hand-picked is a constant across every combination the enumeration will try,
    and a constant in an argmax is not a term: leaving a locked poor Fit in would
    pin the min everywhere and make ``w_minfit`` inert in exactly the mode —
    filling seats — where the searcher most needs it.

    **The seat delta rides inside the cross term**, which is where the objective
    puts it, so a four in which not one cross pair can be read has no delta to
    spend either: the arrangement is then decided by balance alone. That is the
    honest answer rather than a loss — a delta is a difference around a reading,
    and there is no reading for it to be a difference around.
    """

    invariant(
        arrangement.complete,
        "an objective over a line-up with an open seat: three of four is an "
        "honest answer and it is not a lower G, it is no G at all",
    )
    # The **value** form, so the partner seat is narrowed by the raise rather
    # than tested a second time to prove what the line above already
    # guarantees — and so the guarantee survives ``python -O``, which is where
    # an ``assert`` would evaporate.
    partner = invariant(
        arrangement.partner, "a complete four with nobody beside the searcher"
    )
    mode = searcher.mode
    unlocked = tuple(seat for seat in arrangement.seated if not seat.locked)
    crosses = tuple(
        reading
        for pair in arrangement.cross_pairs
        if (
            reading := cross_reading(
                mode, pair.mine.personal, pair.theirs.personal, pair.seat, ruleset
            )
        )
        is not None
    )
    pct, sigma, split = _predicted(
        *_sides(searcher, arrangement), ruleset.balance, combine
    )
    delta = seat_delta(searcher, partner, ruleset)

    values: dict[GroupTerm, float | None] = {
        GroupTerm.BALANCE: balance_norm(pct, ruleset.balance),
        GroupTerm.SEAT_FIT: (
            None
            if not unlocked
            else sum(seat.fit for seat in unlocked) / len(unlocked) / WEIGHT_TOTAL
        ),
        GroupTerm.MIN_SEAT_FIT: (
            None if not unlocked else min(seat.fit for seat in unlocked) / WEIGHT_TOTAL
        ),
        # The delta is signed and the mean is already in `[0, 1]`, so the sum
        # can leave the range at either end. Held inside it, because a term over
        # one would put `G` above a hundred — and the clamp can only bite where
        # the three cross pairs are already at a ceiling the delta has nothing
        # left to add to, or a floor it has nothing left to take.
        GroupTerm.CROSS: (
            None if not crosses else clamp_unit(sum(crosses) / len(crosses) + delta)
        ),
        GroupTerm.CROSS_MIN: None if not crosses else min(crosses),
        GroupTerm.AVAILABILITY: group_availability(
            (searcher.grid, *(seat.grid for seat in arrangement.seated))
        ),
    }

    live = tuple(term for term in GroupTerm if values[term] is not None)
    # Unreachable on today's inputs, exactly as `score`'s twin is: balance reads
    # two Levels and every seated player has one. It is written for the shape
    # rather than for the case — an objective over no evidence is not a low
    # objective, and returning a number for it would be the invented zero this
    # engine refuses everywhere else.
    invariant(
        bool(live),
        "every term of the group objective stood down: an objective over no "
        "evidence is not a low one, it is not an objective",
    )
    shares = renormalised_weights(ruleset.group.weights[mode], live)
    readings = []
    for term in live:
        value = values[term]
        assert value is not None
        readings.append(
            GroupTermReading(
                term=term,
                weight=shares[term],
                value=value,
                contribution=shares[term] * value,
            )
        )
    return GroupScore(
        arrangement=arrangement,
        terms=tuple(readings),
        degraded_terms=tuple(term for term in GroupTerm if values[term] is None),
        # Never provisional: an arrangement has four seats in it by
        # construction, and a line-up with an empty one has no ``G`` to compute.
        forecast=_forecast(pct, sigma, partial=False),
        split=split,
    )


def _sides(
    searcher: Searcher, arrangement: Arrangement
) -> tuple[tuple[LevelReading, ...], tuple[LevelReading, ...]]:
    """The two sides' Levels, in one place, so nothing reads them twice.

    The searcher is on their own side always and by construction — there is no
    arrangement in which they cross the net, because *which side am I on* is not
    a question a builder asks — so what varies is only who is beside them.
    """

    ours = (
        (searcher.level,)
        if arrangement.partner is None
        else (searcher.level, arrangement.partner.level)
    )
    return ours, tuple(opponent.level for opponent in arrangement.opponents)


def arranged(
    searcher: Searcher,
    arrangement: Arrangement,
    ruleset: Ruleset,
    combine: SigmaCombiner,
    *,
    seats_per_side: int = 2,
) -> Arranged:
    """One arrangement's forecast and its side gap. **No objective, deliberately.**

    What a screen draws, for a four **or** for a court still filling. The
    objective needs three seated people and an incomplete line-up has none to
    give it; the forecast does not, because reading a half-empty side *as if the
    missing player matched the one already there* is the whole of what
    ``provisional`` means. So this is the function both cases go through, which
    is what makes *the provisional figure becomes exactly the final figure the
    moment the seat fills* a property of one implementation rather than a hope
    about two (``docs/adr/0108``).
    """

    ours, theirs = _sides(searcher, arrangement)
    pct, sigma, split = _predicted(
        ours, theirs, ruleset.balance, combine, seats_per_side
    )
    return Arranged(
        arrangement=arrangement,
        forecast=_forecast(
            pct,
            sigma,
            partial=len(ours) < seats_per_side or len(theirs) < seats_per_side,
        ),
        split=split,
    )


def arrangements(
    searcher: Searcher,
    seated: Sequence[Seated],
    ruleset: Ruleset,
    combine: SigmaCombiner,
) -> tuple[GroupScore, ...]:
    """All three arrangements of one four, each scored and each with a forecast.

    Returned whole rather than filtered, because the builder is offered all three
    so that swapping sides is a **selection the player makes** and never a
    request they send — *Even it out* is a selection, not a computation, and
    every swap the builder permits is one of these three.
    """

    return tuple(
        objective(searcher, one, ruleset, combine)
        for one in Arrangement.all_of(seated)
    )


def arrange(
    searcher: Searcher,
    seated: Sequence[Seated],
    ruleset: Ruleset,
    combine: SigmaCombiner,
) -> GroupScore:
    """The best arrangement of one four: **``argmax G``, and nothing else.**

    Not a separate step that minimises the level gap and hands the result to the
    objective — that was the shape before ``docs/adr/0117``, and it cannot see
    the seat delta or the cross pairs' seat scopes, both of which change with the
    arrangement. Ties break on the partner's id ascending, so the same four comes
    back the same way round on every process (``docs/adr/0105``).

    Balance outweighs the seat delta by roughly fifty to one, so this will agree
    with :func:`evenest` for any four with a level spread and disagree for a four
    of near-equal levels — **precisely when balance has nothing left to say.**
    That is recorded rather than discovered, so that nobody later finds the delta
    inert and rips it out.
    """

    return best(arrangements(searcher, seated, ruleset, combine))


def best(scores: Sequence[GroupScore]) -> GroupScore:
    """The highest ``G``. Ties break on the partner's id ascending."""

    invariant(bool(scores), "the best of no arrangements at all")
    return sorted(
        scores,
        key=lambda score: (-score.objective, score.arrangement.partner_id),
    )[0]


def evenest(scores: Sequence[GroupScore]) -> GroupScore:
    """The min-gap arrangement — **what *Even it out* selects.**

    A different question from :func:`best`, and the two are separate functions
    because the new fact the builder can state is that they **differ**. Both live
    in the matcher and neither is reimplemented on the client.
    """

    invariant(bool(scores), "the evenest of no arrangements at all")
    return sorted(
        scores,
        key=lambda score: (score.side_gap, score.arrangement.partner_id),
    )[0]


def deciding_reason(winner: GroupScore, runner_up: GroupScore) -> GroupReason:
    """Why this four won, as **one closed code and never a number**.

    ``G`` chose these four over every other combination, and the refusal *never a
    number it cannot explain in one sentence with the evidence named* applies to
    it as much as to a Fit. A second score the player must trust is worse than
    none: it competes with Fit and nobody can act on it. So what crosses is the
    term with the largest margin between the winner and the runner-up — the group
    analogue of the card's top three reasons.

    The margin is over **contributions** rather than values, because a term is
    only as deciding as its weight let it be: a large gap on a six-point term did
    not win the line-up. Ties break on ``GroupTerm``'s declaration order.

    **Its known limit, recorded rather than found later.** Two combinations may
    renormalise on different bases — one four with a blank grid stands
    availability down and spreads its weight over the rest — and a margin taken
    across two bases is then partly an artefact of *which* term went quiet rather
    than of how the two fours differed on it. That is inherent to renormalising
    at all and it is the same property ``G`` itself has; there is no reading that
    escapes it, and pinning the margin to one basis would compare the winner
    against weights it was never scored under. What it costs is bounded: the
    output is a sentence naming a term, never a number, and the winner won on
    ``G`` whichever term this names.
    """

    margins = sorted(
        (
            (
                winner.contribution_of(term) - runner_up.contribution_of(term),
                _GROUP_ORDER[term],
                term,
            )
            for term in GroupTerm
        ),
        key=lambda entry: (-entry[0], entry[1]),
    )
    return margins[0][2].reason


__all__ = [
    "CROSS_TERMS",
    "arrange",
    "arranged",
    "arrangements",
    "best",
    "cross_reading",
    "deciding_reason",
    "evenest",
    "forecast",
    "group_availability",
    "objective",
    "seat_delta",
]
