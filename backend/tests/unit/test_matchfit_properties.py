"""Property tests over a seeded sweep: the bounds, and the monotonicities.

A persona pins one card; an invariant pins one identity. These walk a *range* of
inputs and assert the shape of the answer over all of them — the third leg
ADR-0015 prescribes, and the one that catches a curve which is right at both ends
and wrong in the middle.

**Seeded, and the seed is written down.** A property that fails on Tuesday and passes
on Wednesday is not a property; ``random.Random(SEED)`` gives the same sweep on every
machine and every run, and widening the sweep is a diff on a number here.

The sweep is over *declarations, prices and start times*, never over ratings, because
no term in this slice reads a Level. That is the honest shape of the thing being
tested and it is why this file is shorter than the pairing engine's: three of Match
Fit's ten terms are still owed (#85, #86).
"""

import random
from dataclasses import replace

import pytest

from app.engines.fit import ExcludedTerm, ScoredTerm, TermCode, TermKind
from app.engines.matchfit.core import measured_share, renormalise, whole_percent
from app.engines.matchfit.v1 import CONSTANTS, MatchFitEngineV1
from app.engines.matchmaking import (
    LadderQualification,
    MatchSnapshot,
    MatchTypePreference,
    PlayerProfile,
    PlayerRef,
    PlayHistory,
    Weekday,
)
from app.kernel import grosze, ratio
from tests.unit.matchmaking_snapshots import (
    NOW,
    WARSAW,
    analysis,
    doubles,
    profile,
    singles,
    skill,
    starting,
    window,
    with_records,
)

#: The seed. Written down so the sweep is the same everywhere, and so widening it is
#: a reviewable change rather than a different run.
SEED = 20260817

#: How many draws each property below is asserted over. Large enough to cross every
#: branch of every curve many times, small enough that the whole file is milliseconds.
DRAWS = 400

ENGINE = MatchFitEngineV1()

ADA = skill("ada", 300, 20)
BO = skill("bo", 315, 25)
CY = skill("cy", 285, 30)
DEE = skill("dee", 330, 60)

LADDERS = tuple(LadderQualification)
PREFERENCES = (None, MatchTypePreference.COMPETITIVE, MatchTypePreference.SOCIAL)

#: Declarations of *when*, from silence to a single Tuesday morning. Drawn beside
#: the prices and the distances so that the time term is crossed on both sides of
#: both of its halves — the right day at the wrong hour and the wrong day at the
#: right one — rather than only where a hand-written case happened to look.
DAYS = (
    None,
    frozenset({Weekday.TUESDAY}),
    frozenset({Weekday.SATURDAY, Weekday.SUNDAY}),
    frozenset(Weekday),
)
HOURS = (None, (window(6, 9),), (window(18, 22),), (window(6, 9), window(18, 22)))


def scored(snapshot: MatchSnapshot, declaration: PlayerProfile):
    return ENGINE.score(
        snapshot=snapshot, profile=declaration, analysis=analysis(), now=NOW
    )


def drawn(seed: int = SEED):
    """A sweep of (match, declaration) pairs: prices, distances, kinds and ladders.

    Prices run from free to five times the seat share and distances from next door
    to two hours, so every curve is crossed inside its limit, just past it, halfway
    down its span and floored — rather than at whichever point a hand-written case
    happened to pick.
    """

    rng = random.Random(seed)
    for _ in range(DRAWS):
        payable = rng.randrange(0, 11_000, 50)
        snapshot = replace(
            doubles(
                ADA,
                BO,
                CY,
                DEE,
                travel_minutes=rng.randrange(0, 120),
                counted=rng.choice((True, False)),
                ladder=rng.choice(LADDERS),
                start=starting(day=rng.randrange(0, 7), hour=rng.randrange(0, 24)),
            ),
            seat_share=grosze(max(payable, 2150)),
            payable=grosze(payable),
        )
        declaration = profile(
            ceiling=rng.choice((None, *range(0, 6000, 250))),
            radius=rng.choice((None, *range(0, 90, 5))),
            match_type=rng.choice(PREFERENCES),
            days=rng.choice(DAYS),
            hours=rng.choice(HOURS),
        )
        yield snapshot, declaration


def test_the_sweep_reaches_every_branch_of_every_curve():
    """A sweep that has quietly lost half its inputs passes by finding nothing.

    Counted, so a narrowed draw range shows up as a red test rather than as a
    property that holds because it was never exercised.
    """

    values: dict[TermCode, set[str]] = {code: set() for code in CONSTANTS.weights}
    for snapshot, declaration in drawn():
        for term in scored(snapshot, declaration).terms:
            if isinstance(term, ScoredTerm):
                edge = "full" if term.value == 1 else "part"
                values[term.code].add("zero" if term.value == 0 else edge)
            else:
                values[term.code].add("excluded")

    assert values[TermCode.TIME_FIT] == {"full", "part"}
    assert values[TermCode.PRICE] == {"full", "part", "zero"}
    assert values[TermCode.TRAVEL] == {"full", "part", "zero"}
    assert values[TermCode.MATCH_TYPE] == {"full", "part"}
    assert values[TermCode.LADDER_QUALIFICATION] == {"full", "part"}
    assert values[TermCode.GROUP_RELIABILITY] == {"excluded"}
    assert values[TermCode.FAMILIARITY] == {"excluded"}


# --- The bounds -------------------------------------------------------------------


def test_every_figure_stays_inside_its_range():
    for snapshot, declaration in drawn():
        result = scored(snapshot, declaration)
        assert 0 <= result.fit <= 100
        assert 0 <= result.coverage <= 100
        assert all(0 <= term.value <= 1 for term in result.scored)


def test_the_score_is_always_the_weighted_average_of_the_terms_that_ran():
    """The identity, over the sweep rather than over the written-out shapes."""

    for snapshot, declaration in drawn():
        result = scored(snapshot, declaration)
        shares = renormalise(result.scored)
        pairs = zip(shares, result.scored, strict=True)
        expected = sum((share * term.value for share, term in pairs), ratio(0, 1))
        assert result.fit == whole_percent(expected)
        assert result.coverage == whole_percent(measured_share(result.terms))


def test_the_score_never_leaves_the_range_so_a_clamp_could_not_bind():
    """Why there is no display clamp at the end of the engine.

    The source design clamped because its ``+8`` / ``−8`` modifiers pushed the score
    outside 0–100 first. With every signal inside the weighting, the fit is a weighted
    average of values in 0..1 and *cannot* leave the range — so a clamp is a guard
    that could never fire, and a guard that cannot fire is one nobody should watch.
    """

    extremes = (
        (grosze(0), 0),
        (grosze(100_000), 240),
    )
    for payable, away in extremes:
        snapshot = replace(
            doubles(ADA, BO, CY, DEE, travel_minutes=away),
            seat_share=grosze(max(int(payable), 1)),
            payable=payable,
        )
        for declaration in (profile(), profile(ceiling=1, radius=0)):
            assert 0 <= scored(snapshot, declaration).fit <= 100


# --- The monotonicities -----------------------------------------------------------


@pytest.mark.parametrize("ceiling", [None, 0, 1000, 2150, 5000])
def test_a_dearer_seat_never_scores_higher_on_price(ceiling):
    """Monotone non-increasing in the payable, at every declared ceiling.

    Including no ceiling at all, where the term is flat at full marks — which is the
    case that would break if a *default* ceiling ever crept back in.
    """

    declaration = profile(ceiling=ceiling)
    values = []
    for payable in range(0, 8000, 50):
        snapshot = replace(
            doubles(ADA, BO, CY, DEE),
            seat_share=grosze(max(payable, 1)),
            payable=grosze(payable),
        )
        term = next(
            item
            for item in scored(snapshot, declaration).terms
            if item.code is TermCode.PRICE
        )
        assert isinstance(term, ScoredTerm)
        values.append(term.value)
    assert values == sorted(values, reverse=True)


@pytest.mark.parametrize("radius", [None, 0, 15, 40])
def test_a_longer_journey_never_scores_higher_on_travel(radius):
    declaration = profile(radius=radius)
    values = []
    for away in range(0, 150):
        snapshot = doubles(ADA, BO, CY, DEE, travel_minutes=away)
        term = next(
            item
            for item in scored(snapshot, declaration).terms
            if item.code is TermCode.TRAVEL
        )
        assert isinstance(term, ScoredTerm)
        values.append(term.value)
    assert values == sorted(values, reverse=True)


def test_a_match_inside_a_declared_limit_always_scores_full_marks():
    """No partial credit for being *nearly* at the ceiling: at or within is within."""

    for ceiling in range(0, 6000, 250):
        snapshot = replace(
            doubles(ADA, BO, CY, DEE),
            seat_share=grosze(max(ceiling, 1)),
            payable=grosze(ceiling),
        )
        result = scored(snapshot, profile(ceiling=ceiling, radius=999))
        assert all(term.value == 1 for term in result.scored)
        assert result.fit == 100


def test_declaring_a_limit_never_raises_a_score():
    """An undeclared limit scores full marks, so declaring one can only cost.

    The property that says a constraint term is a *constraint*: it is the shape of a
    limit rather than a bonus for having one, and a term that rewarded a declaration
    would give players a reason to declare things they do not mean.

    The comparison is against the *same match* seen by a player who declared nothing,
    not against a fixed 100: the ladder term reads a fact the **match** carries, so a
    silent player still scores below full marks on a match outside their ladder.
    """

    for snapshot, declaration in drawn():
        assert scored(snapshot, declaration).fit <= scored(snapshot, profile()).fit


def test_coverage_never_moves_with_a_declaration():
    """*A missing declaration is not a missing measurement*, over the whole sweep."""

    baseline = None
    for snapshot, declaration in drawn():
        coverage = scored(snapshot, declaration).coverage
        baseline = coverage if baseline is None else baseline
        assert coverage == baseline


def test_more_evidence_never_lowers_coverage():
    """Coverage rises with every record the platform actually has.

    Nought, one, two and three of the other seated players carrying a record, then
    the play history on top: coverage is monotone in how much was observed, which is
    the property that makes it readable as *how much of this was measured*.
    """

    match = doubles(ADA, BO, CY, DEE)
    steps = (
        with_records(match, None, None, None, None),
        with_records(match, None, 90, None, None),
        with_records(match, None, 90, 90, None),
        with_records(match, None, 90, 90, 90),
        replace(
            with_records(match, None, 90, 90, 90),
            history=PlayHistory(played_recently=frozenset()),
        ),
    )
    coverages = [scored(step, profile()).coverage for step in steps]
    assert coverages == sorted(coverages)
    assert coverages[0] < coverages[-1] == 100


def test_a_more_reliable_group_never_scores_lower():
    """Monotone in the observation, which is the whole of the dark term's curve."""

    fits = []
    for rate in range(0, 101, 5):
        group = replace(
            with_records(doubles(ADA, BO, CY, DEE), None, rate, rate, rate),
            history=PlayHistory(played_recently=frozenset()),
        )
        fits.append(scored(group, profile()).fit)
    assert fits == sorted(fits)


def test_more_new_faces_never_scores_lower_on_familiarity():
    """Variety rewarded, monotonically, with no constant of its own to tune."""

    everybody = (PlayerRef("bo"), PlayerRef("cy"), PlayerRef("dee"))
    values = []
    for repeats in range(len(everybody), -1, -1):
        group = replace(
            doubles(ADA, BO, CY, DEE),
            history=PlayHistory(played_recently=frozenset(everybody[:repeats])),
        )
        term = next(
            item
            for item in scored(group, profile()).terms
            if item.code is TermCode.FAMILIARITY
        )
        assert isinstance(term, ScoredTerm)
        values.append(term.value)
    assert values == sorted(values)
    assert values == [ratio(0, 1), ratio(1, 3), ratio(2, 3), ratio(1, 1)]


def test_the_time_term_is_two_valued_and_never_decays():
    """Full marks or the mismatch value, and nothing in between, over 400 draws.

    Price and travel decay because *how far over* is a quantity; being at work is
    not. A curve creeping in here — half marks for an hour early, say — would be a
    third kind of constant with no measurement behind it, and it would show up as a
    third value in this set.
    """

    seen = set()
    for snapshot, declaration in drawn():
        for term in scored(snapshot, declaration).terms:
            if term.code is TermCode.TIME_FIT:
                assert isinstance(term, ScoredTerm)
                seen.add(term.value)
    assert seen == {ratio(1, 1), CONSTANTS.time_outside}


@pytest.mark.parametrize(
    "days, hours",
    [
        (None, None),
        (frozenset({Weekday.TUESDAY, Weekday.THURSDAY}), None),
        (None, (window(18, 22),)),
        (frozenset({Weekday.TUESDAY}), (window(6, 9), window(18, 22))),
    ],
    ids=["nothing", "days only", "hours only", "both"],
)
def test_the_whole_week_agrees_with_the_rule_written_out_independently(days, hours):
    """The oracle: 168 starts, an hour apart, against the rule stated in English.

    *Inside the declaration* is **on a declared day and starting inside a declared
    window**, with a silence on either half meaning *any*. That sentence is written
    out here in plain Python — set membership and a half-open comparison on the
    local minute — so the engine and this file agree only if both are right. A term
    reading the wrong half, comparing against the wrong end of a window, or reading
    a weekday off the UTC instant disagrees somewhere in the week.
    """

    declaration = profile(days=days, hours=hours)
    for day in range(7):
        for hour in range(24):
            start = starting(day=day, hour=hour)
            local = start.astimezone(WARSAW)
            inside_days = days is None or Weekday(local.isoweekday()) in days
            minute = local.hour * 60 + local.minute
            inside_hours = hours is None or any(
                one.start <= minute < one.end for one in hours
            )
            inside = inside_days and inside_hours
            expected = ratio(1, 1) if inside else CONSTANTS.time_outside
            term = next(
                item
                for item in scored(
                    doubles(ADA, BO, CY, DEE, start=start), declaration
                ).terms
                if item.code is TermCode.TIME_FIT
            )
            assert isinstance(term, ScoredTerm)
            assert term.value == expected, (day, hour)


# --- Absence, over the sweep ------------------------------------------------------


def test_absence_never_beats_full_marks_anywhere_in_the_sweep():
    """**Absence never flatters**, asserted over 400 draws rather than four shapes."""

    for snapshot, declaration in drawn():
        dark = scored(snapshot, declaration)
        lit = scored(
            replace(
                with_records(snapshot, None, 100, 100, 100),
                history=PlayHistory(played_recently=frozenset()),
            ),
            declaration,
        )
        assert dark.fit <= lit.fit
        assert dark.coverage < lit.coverage


def test_an_excluded_term_keeps_its_weight_and_never_gains_a_value():
    for snapshot, declaration in drawn():
        for term in scored(snapshot, declaration).terms:
            if isinstance(term, ExcludedTerm):
                assert term.weight == CONSTANTS.weights[term.code]
                assert term.kind is TermKind.EVIDENCE
                assert not hasattr(term, "value")


def test_a_constraint_never_drops_out_of_the_score():
    for snapshot, declaration in drawn():
        result = scored(snapshot, declaration)
        constraints = [
            term for term in result.terms if term.kind is TermKind.CONSTRAINT
        ]
        assert len(constraints) == 5
        assert all(isinstance(term, ScoredTerm) for term in constraints)


def test_both_arities_reach_the_same_terms():
    """Nothing in this table is about how many people play, so nothing here is.

    Asserted because it is the kind of thing that quietly stops being true: the two
    evidence terms read *the other seated players*, and a singles match has one.
    """

    for arity in (singles(ADA, BO), doubles(ADA, BO, CY, DEE)):
        result = scored(arity, profile())
        assert [term.code for term in result.terms] == list(CONSTANTS.weights)

    solo = replace(
        with_records(singles(ADA, BO), None, 60),
        history=PlayHistory(played_recently=frozenset({PlayerRef("bo")})),
    )
    result = scored(solo, profile())
    assert result.coverage == 100
    assert next(
        term for term in result.terms if term.code is TermCode.FAMILIARITY
    ).value == ratio(0, 1)
