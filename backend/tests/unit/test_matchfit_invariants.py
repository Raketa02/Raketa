"""What must still be true after any constant retune.

The opposite file to ``test_matchfit_personas.py``. Nothing here reads a literal a
constant owns: every assertion is either structural — the score is the weighted
average of its own terms — or it reads the constant it is about. A retune that breaks
one of these has broken the model, not the baseline.

**The one claim in the spec that is false is reported here rather than dressed in a
weaker test's name.** The issue asks for *"an invariant test that excluding a term
never raises a score"*. Under renormalisation it cannot hold, and the counterexample
is named, argued and pinned below beside the invariant that is true — exclusion never
does better than including the term at full marks, which is exactly the regression
ADR-0027 exists to close.
"""

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from enum import Enum
from fractions import Fraction
from pathlib import Path

import pytest

from app.engines.fit import (
    BalanceFact,
    ExcludedTerm,
    FamiliarityFact,
    LadderFact,
    MatchFitEngine,
    MatchFitScore,
    MatchTypeFact,
    PriceFact,
    ReliabilityFact,
    ScoredTerm,
    SkillOverlapFact,
    TermCode,
    TermKind,
    TimeFact,
    TravelFact,
    ViabilityFact,
)
from app.engines.forecast import Certainty, PairingAnalysis
from app.engines.matchfit.core import (
    FULL_MARKS,
    NO_MARKS,
    Observed,
    constraint_term,
    decayed,
    evidence_term,
    lowest_contribution,
    measured_share,
    ranked_by_contribution,
    renormalise,
    weighted_value,
    whole_percent,
)
from app.engines.matchfit.v1 import (
    CONSTANTS,
    ENGINE_VERSION,
    PENDING_WEIGHTS,
    WEIGHT_TOTAL,
    MatchFitConstants,
    MatchFitEngineV1,
)
from app.engines.matchmaking import (
    HOLD_LADDER,
    ClubSnapshot,
    CourtHold,
    HourWindow,
    LadderQualification,
    MatchPhase,
    MatchSnapshot,
    MatchTypePreference,
    PlayerProfile,
    PlayerRef,
    PlayerScore,
    PlayHistory,
    SeatState,
    Weekday,
    level,
)
from app.kernel import (
    InvariantViolated,
    Ratio,
    Zone,
    apply_fraction,
    grosze,
    instant,
    local_iso_weekday,
    local_minute_of_day,
    minutes,
    ratio,
    shifted,
)
from tests.unit.matchmaking_snapshots import (
    NOW,
    WARSAW,
    analysis,
    doubles,
    profile,
    singles,
    skill,
    starting,
    unrated,
    window,
    with_records,
)

ROOT = Path(__file__).resolve().parents[2]
MATCHFIT = ROOT / "app" / "engines" / "matchfit"
FIT = ROOT / "app" / "engines" / "fit.py"

ENGINE = MatchFitEngineV1()

ADA = skill("ada", 300, 20)
BO = skill("bo", 315, 25)
CY = skill("cy", 285, 30)
DEE = skill("dee", 330, 60)

#: The three shapes a hand-built pairing analysis comes in, which is one per state
#: the two terms that read it can be in: a full match with a band around it, a match
#: one seat from full with that seat solved exactly, and a court with nothing in it
#: to aim at. Every case below is paired with the one its match would actually have
#: got, so no shape in the sweep describes a world the pairing engine cannot produce.
AIMED = analysis(estimate=100, band=300)
AIMED_AT_THE_SEAT = analysis(estimate=100, seat_target=300)
UNAIMED = analysis()

#: One well-formed padel match, one singles match, one court nobody has joined —
#: crossed with declarations that satisfy, breach and omit every constraint the
#: table has, and with the pairing analysis each would have been given. Written out
#: rather than drawn at random, because an invariant that only holds for the inputs
#: a seed happened to pick is not an invariant.
CASES: tuple[tuple[str, MatchSnapshot, PlayerProfile, PairingAnalysis], ...] = (
    ("declared nothing, full padel", doubles(ADA, BO, CY, DEE), profile(), AIMED),
    (
        "declared nothing, empty court",
        doubles(None, None, None, None, viewer=ADA),
        profile(),
        UNAIMED,
    ),
    ("declared nothing, singles", singles(ADA, BO), profile(), AIMED),
    (
        "everything satisfied",
        doubles(ADA, BO, CY, None),
        profile(
            ceiling=2500,
            radius=20,
            match_type=MatchTypePreference.COMPETITIVE,
            days=frozenset({Weekday.TUESDAY, Weekday.SATURDAY}),
            hours=(window(18, 22),),
            appetite=2,
        ),
        AIMED_AT_THE_SEAT,
    ),
    (
        "on a day they did not declare",
        doubles(ADA, BO, CY, None),
        profile(days=frozenset({Weekday.SATURDAY, Weekday.SUNDAY})),
        AIMED_AT_THE_SEAT,
    ),
    (
        "at an hour they did not declare",
        doubles(ADA, BO, CY, None),
        profile(days=frozenset({Weekday.TUESDAY}), hours=(window(6, 9),)),
        AIMED_AT_THE_SEAT,
    ),
    (
        "over the ceiling",
        doubles(ADA, BO, CY, None),
        profile(ceiling=1800, radius=20),
        AIMED_AT_THE_SEAT,
    ),
    (
        "far past the ceiling",
        doubles(ADA, BO, CY, None),
        profile(ceiling=500, radius=20),
        AIMED_AT_THE_SEAT,
    ),
    (
        "beyond the radius",
        doubles(ADA, BO, CY, None, travel_minutes=35),
        profile(ceiling=2500, radius=20),
        AIMED_AT_THE_SEAT,
    ),
    (
        "far beyond the radius",
        doubles(ADA, BO, CY, None, travel_minutes=90),
        profile(ceiling=2500, radius=5),
        AIMED_AT_THE_SEAT,
    ),
    (
        "wanted social, got counted",
        doubles(ADA, BO, CY, None, counted=True),
        profile(match_type=MatchTypePreference.SOCIAL),
        AIMED_AT_THE_SEAT,
    ),
    (
        "wanted counted, got a friendly",
        doubles(ADA, BO, CY, None, counted=False),
        profile(match_type=MatchTypePreference.COMPETITIVE),
        AIMED_AT_THE_SEAT,
    ),
    (
        "in a ladder this does not count for",
        doubles(ADA, BO, CY, None, ladder=LadderQualification.OUTSIDE),
        profile(),
        AIMED_AT_THE_SEAT,
    ),
    (
        "in a ladder and it counts",
        doubles(ADA, BO, CY, None, ladder=LadderQualification.QUALIFIES),
        profile(),
        AIMED_AT_THE_SEAT,
    ),
    (
        "no court held at a club with nothing left",
        doubles(ADA, BO, CY, None, hold=CourtHold.NONE, crowding=100),
        profile(),
        AIMED_AT_THE_SEAT,
    ),
    (
        "half an hour from the cutoff with three seats open",
        doubles(ADA, None, None, None, cutoff=shifted(NOW, minutes(30))),
        profile(),
        AIMED,
    ),
    (
        "the dark terms lit",
        replace(
            with_records(doubles(ADA, BO, CY, DEE), None, 95, 80, 100),
            history=PlayHistory(played_recently=frozenset({PlayerRef("bo")})),
        ),
        profile(ceiling=2500, radius=20),
        AIMED,
    ),
    (
        "the dark terms lit and bad",
        replace(
            with_records(doubles(ADA, BO, CY, DEE), None, 10, 5, 20),
            history=PlayHistory(
                played_recently=frozenset({PlayerRef("bo"), PlayerRef("cy")})
            ),
        ),
        profile(),
        AIMED,
    ),
    (
        "aimed a whole band away",
        doubles(ADA, BO, CY, DEE),
        profile(),
        analysis(estimate=100, band=410),
    ),
    (
        "aimed from a band rather than a seat",
        doubles(ADA, BO, CY, None),
        profile(),
        analysis(estimate=88, band=340),
    ),
    (
        "forecast at the floor of the scale",
        doubles(ADA, BO, CY, DEE),
        profile(),
        analysis(estimate=35, band=300),
    ),
    (
        "forecast too uncertain to print",
        doubles(ADA, BO, CY, DEE),
        profile(),
        analysis(
            estimate=78,
            margin=30,
            certainty=Certainty.LOW,
            imputed_seats=3,
            band=300,
        ),
    ),
    (
        "a viewer this sport has never rated",
        doubles(ADA, BO, CY, DEE, viewer=unrated("newcomer")),
        profile(),
        AIMED,
    ),
)

IDS = [name for name, _, _, _ in CASES]


def scored(
    snapshot: MatchSnapshot,
    declaration: PlayerProfile,
    aim: PairingAnalysis = AIMED,
) -> MatchFitScore:
    return ENGINE.score(snapshot=snapshot, profile=declaration, analysis=aim, now=NOW)


@pytest.fixture(params=CASES, ids=IDS)
def shape(request) -> tuple[str, MatchSnapshot, PlayerProfile, PairingAnalysis]:
    """One (match, declaration, analysis) triple from the sweep."""

    return request.param


@pytest.fixture
def case(shape) -> MatchFitScore:
    """That triple, scored. Two fixtures rather than one, so the handful of tests
    that need the *inputs* take ``shape`` beside it instead of reverse-engineering
    which case they were handed."""

    _, snapshot, declaration, aim = shape
    return scored(snapshot, declaration, aim)


def test_the_invariants_below_are_asserted_over_every_shape():
    """A sweep that has quietly lost half its inputs passes by finding nothing.

    Every branch of every term is in here: each constraint satisfied, breached
    mildly, breached past its span and undeclared; both dark evidence terms absent,
    lit well and lit badly; viability at both ends of both of its halves — a booked
    court and none at a full club, a match a day from its cutoff and one half an
    hour from it with three seats open; and the two terms that read the pairing
    analysis at every state they have — aimed exactly, aimed from a band, aimed a
    whole band away, forecast even, forecast at the floor, forecast too uncertain to
    print, and both excluded for want of anything to aim at or anybody to aim.
    """

    assert len(CASES) == 23, IDS
    assert len(set(IDS)) == len(IDS), IDS


# --- The score, and the coverage that is not part of it --------------------------


def test_the_score_is_the_weighted_average_of_its_own_terms(case):
    """The identity the two carried numbers exist to satisfy.

    ``fit`` and ``coverage`` are fields rather than properties, for the same reason
    the split bar is a field on a ``BalanceForecast``: the derivation goes through
    the engine's rounding, and a property recomputing it here would be a second
    implementation of the rounding rule. So the derivation is asserted instead, over
    every shape, from the term list the score itself carries.
    """

    assert case.fit == whole_percent(weighted_value(case.scored))
    assert case.coverage == whole_percent(measured_share(case.terms))


def test_the_renormalised_weights_sum_to_exactly_one(case):
    """Exactly, and not to 0,9999999999999999.

    The weights are integers and the shares are rationals, so this is an equality a
    test can assert rather than a tolerance it has to pick — which is the reason the
    whole engine computes in ``Ratio`` and crosses into a percent once.
    """

    shares = renormalise(case.scored)
    assert sum(shares) == 1
    assert len(shares) == len(case.scored)


def test_coverage_is_the_weight_that_ran_over_the_whole_table(case):
    ran = sum(term.weight for term in case.scored)
    table = sum(term.weight for term in case.terms)
    assert measured_share(case.terms) == ratio(ran, table)
    assert table == sum(CONSTANTS.weights.values())


def test_coverage_is_never_blended_into_the_score():
    """Two numbers, and the second is not a discount on the first.

    The same match seen twice: once with both dark terms absent, once with both lit
    at **full marks**. Every scored value is identical, so the fit must not move —
    while coverage goes from part of the table to all of it. A design that folded
    coverage in would move both.
    """

    thin = doubles(ADA, BO, CY, DEE)
    full = replace(
        with_records(thin, None, 100, 100, 100),
        history=PlayHistory(played_recently=frozenset()),
    )
    declaration = profile(ceiling=2500, radius=20)
    assert scored(thin, declaration).fit == scored(full, declaration).fit
    assert scored(thin, declaration).coverage < scored(full, declaration).coverage
    assert scored(full, declaration).coverage == 100


def test_absence_never_scores_better_than_full_marks(shape):
    """**Absence never flatters.** The invariant ADR-0027 is actually about.

    The regression it records is that the source design scored absent evidence at
    ``1,0`` and kept its weight, which made the score monotonically *decreasing* in
    information. So the claim that must hold is a comparison against that design:
    excluding a term can never beat including it at full marks. It is arithmetic —
    the average of the rest is at most one, so admitting a one into the average
    cannot lower it — and it is the whole guarantee, asserted over every shape rather
    than argued once.
    """

    _, snapshot, declaration, aim = shape
    absent = scored(_dark(snapshot), declaration, aim)
    present = scored(_lit(snapshot), declaration, aim)
    assert absent.fit <= present.fit
    assert absent.coverage <= present.coverage


def test_excluding_a_term_can_raise_the_number_and_that_is_not_a_bug():
    """The spec's *"excluding a term never raises a score"* is false, and this is why.

    A renormalised score is the weighted average of the terms that ran. Drop a term
    whose value was *below* that average and the average goes **up** — necessarily,
    for the same reason removing the lowest mark raises a mean. Here a group nobody
    turns up for scores 0,10 on reliability, and losing that observation entirely
    takes the fit from 74 to 100.

    No arrangement of the mechanism makes the literal claim true. Scoring absent
    evidence at zero and keeping its weight would satisfy it, and that is the
    *penalty* alternative ADR-0027 rejected by name — it makes a thin score and a
    genuinely bad score indistinguishable, which is the same collapse in the other
    direction. So the guarantee is the pair: exclusion can never beat full marks, and
    coverage falls whenever anything is excluded. Either number alone misleads, which
    is precisely why the engine reports both and blends neither.
    """

    match = doubles(ADA, BO, CY, DEE)
    bad_news = replace(
        with_records(match, None, 10, 10, 10),
        history=PlayHistory(played_recently=frozenset()),
    )
    declaration = profile(ceiling=2500, radius=20)
    knowing = scored(bad_news, declaration)
    not_knowing = scored(match, declaration)

    assert knowing.fit < not_knowing.fit
    assert knowing.coverage > not_knowing.coverage


@pytest.mark.parametrize("name, snapshot, declaration, aim", CASES, ids=IDS)
def test_excluding_a_term_always_lowers_coverage(name, snapshot, declaration, aim):
    """The half of the guarantee that *is* monotone, and it has to be.

    Coverage is what makes a thin score legible, so it must fall whenever anything
    was not measured — for every shape, with no exception for the shapes where the
    fit happens to look fine.
    """

    result = scored(snapshot, declaration, aim)
    missing = sum(term.weight for term in result.excluded)
    if missing:
        assert result.coverage < 100
    else:
        assert result.coverage == 100


def _dark(snapshot: MatchSnapshot) -> MatchSnapshot:
    """The same match with both dark fields absent — every real snapshot today."""

    return replace(
        with_records(snapshot, *(None for _ in snapshot.seats)), history=None
    )


def _lit(snapshot: MatchSnapshot) -> MatchSnapshot:
    """The same match with both dark terms observable and at **full marks**.

    Everybody who is not the current player turns up every time, and the current
    player has played none of them. This is the state the source design *assumed*,
    and the comparison against it is what *absence never flatters* means.
    """

    current = snapshot.current_player.player
    return replace(
        with_records(
            snapshot,
            *(
                100
                if seat.occupant is not None and seat.occupant.player != current
                else None
                for seat in snapshot.seats
            ),
        ),
        history=PlayHistory(played_recently=frozenset()),
    )


# --- Term kinds, and what each one does with a silence ---------------------------


def test_a_constraint_term_always_runs_and_an_absent_declaration_is_full_marks(case):
    """*A missing declaration is not a missing measurement.*

    Every constraint in the table scores on every shape, and a player who declared
    nothing scores full marks on all of them — keeping the weight, leaving coverage
    exactly where it was.
    """

    constraints = [term for term in case.terms if term.kind is TermKind.CONSTRAINT]
    assert [term.code for term in constraints] == [
        code
        for code in CONSTANTS.weights
        if code
        not in (
            TermCode.SKILL_OVERLAP,
            TermCode.PREDICTED_BALANCE,
            TermCode.MATCH_VIABILITY,
            TermCode.GROUP_RELIABILITY,
            TermCode.FAMILIARITY,
        )
    ]
    assert all(isinstance(term, ScoredTerm) for term in constraints)


def test_a_player_who_declared_nothing_has_the_same_coverage_as_one_who_declared_all():
    """The constraint rule, as the only measurement that could show it broken.

    If an absent declaration were treated as absent *evidence*, a silent player's
    matches would all be scored thinly. Coverage is what would say so, and it does
    not move.
    """

    match = doubles(ADA, BO, CY, None)
    silent = scored(match, profile())
    declared = scored(
        match,
        profile(
            ceiling=2500,
            radius=20,
            match_type=MatchTypePreference.COMPETITIVE,
            days=frozenset({Weekday.TUESDAY}),
            hours=(window(18, 22),),
        ),
    )
    breached = scored(
        match, profile(days=frozenset({Weekday.SUNDAY}), hours=(window(6, 9),))
    )
    assert silent.coverage == declared.coverage == breached.coverage
    # 100 no longer, and viability is why: this match is three-quarters paid, so the
    # one evidence term that always runs scores below full marks and a player who
    # declared nothing is told something true about the match rather than nothing at
    # all. Read off the term rather than written down, because the figure is a
    # constant's and this file is the one that must survive a retune.
    viability = _term(silent, TermCode.MATCH_VIABILITY)
    assert isinstance(viability, ScoredTerm)
    assert viability.value < 1
    assert all(
        term.value == 1
        for term in silent.scored
        if term.code is not TermCode.MATCH_VIABILITY
    )


def test_an_evidence_term_with_nothing_observed_is_excluded_and_not_scored_well():
    """The reclassification the whole spec turns on, at its smallest.

    Both **dark** evidence terms are absent on every snapshot the platform can
    assemble today, so they are *excluded*: no value, no payload, weight still in
    coverage's denominator. There is no field on an ``ExcludedTerm`` for a friendly
    default to be written into, which is the difference between this and a
    convention.
    """

    result = scored(doubles(ADA, BO, CY, DEE), profile())
    dark = [term for term in result.terms if isinstance(term, ExcludedTerm)]
    assert [term.code for term in dark] == [
        TermCode.GROUP_RELIABILITY,
        TermCode.FAMILIARITY,
    ]
    assert all(term.kind is TermKind.EVIDENCE for term in dark)
    assert all(not hasattr(term, "value") for term in dark)


def test_only_evidence_is_ever_excluded():
    """``constraint_term`` returns a ``ScoredTerm``, so there is no other outcome.

    Asserted through the builder rather than over the engine's output, because it is
    a claim about what is *writable*: a constraint cannot become an exclusion without
    somebody changing this function's return type.
    """

    term = constraint_term(
        TermCode.PRICE, 6, NO_MARKS, PriceFact(payable=grosze(1), ceiling=None)
    )
    assert isinstance(term, ScoredTerm)
    assert term.kind is TermKind.CONSTRAINT
    assert ExcludedTerm(code=TermCode.FAMILIARITY, weight=3).kind is TermKind.EVIDENCE


def test_no_term_in_the_table_is_left_carrying_a_fabricated_default():
    """**The table is complete and nothing in it invents an observation.**

    The claim ADR-0027 exists for, at the only size it can be checked: for every
    evidence term there is an input under which it comes back *excluded*, so no term
    is quietly scoring a figure the platform never had. Written as a loop over the
    table rather than as four named cases, because the failure mode is a *new* term
    landing with a friendly fallback — and a loop notices that where a written-out
    list does not.

    **Viability is the one exception and is asserted as one.** It cannot be taken
    away, because every match has a phase, a hold, a seat count and a cutoff — and
    that is not a default, it is a measurement that is always available. A term that
    could never be excluded *and* had no such fact behind it would be exactly the
    fabrication this test is looking for, so the exception is named here rather than
    left to be inferred from the loop's silence.
    """

    lit = replace(
        with_records(doubles(ADA, BO, CY, DEE), None, 90, 90, 90),
        history=PlayHistory(played_recently=frozenset()),
    )
    full = scored(lit, profile(), AIMED)
    assert full.coverage == 100

    strippable = {
        TermCode.SKILL_OVERLAP: (lit, analysis(estimate=90)),
        TermCode.PREDICTED_BALANCE: (lit, analysis(band=300)),
        TermCode.GROUP_RELIABILITY: (
            with_records(lit, None, None, None, None),
            AIMED,
        ),
        TermCode.FAMILIARITY: (replace(lit, history=None), AIMED),
    }
    evidence = [term.code for term in full.terms if term.kind is TermKind.EVIDENCE]
    assert set(evidence) == set(strippable) | {TermCode.MATCH_VIABILITY}

    for code, (snapshot, aim) in strippable.items():
        assert isinstance(_term(scored(snapshot, profile(), aim), code), ExcludedTerm)

    # And the exception, stated rather than inferred: nothing about a match can take
    # viability away, which is why it is the term that closes the ordering regression.
    hopeless = doubles(None, None, None, None, viewer=ADA, hold=CourtHold.NONE)
    assert isinstance(
        _term(scored(hopeless, profile(), UNAIMED), TermCode.MATCH_VIABILITY),
        ScoredTerm,
    )


def test_an_evidence_term_carries_its_observation_whole_or_not_at_all():
    """A value and its payload arrive together, the way a rating does."""

    fact = FamiliarityFact(new_faces=1, others=2)
    assert isinstance(evidence_term(TermCode.FAMILIARITY, 3, None), ExcludedTerm)
    lit = evidence_term(TermCode.FAMILIARITY, 3, Observed(value=ratio(1, 2), fact=fact))
    assert isinstance(lit, ScoredTerm)
    assert (lit.value, lit.fact) == (ratio(1, 2), fact)


def test_every_term_carries_a_positive_weight_and_a_value_inside_its_range(case):
    for term in case.terms:
        assert term.weight > 0
        if isinstance(term, ScoredTerm):
            assert 0 <= term.value <= 1
            assert term.fact.kind == term.code.value
    assert 0 <= case.fit <= 100
    assert 0 <= case.coverage <= 100


def test_one_term_per_code_and_every_code_in_the_table(case):
    assert [term.code for term in case.terms] == list(CONSTANTS.weights)
    assert all(term.weight == CONSTANTS.weights[term.code] for term in case.terms)


# --- Reasons and the one warning -------------------------------------------------


def test_reasons_are_ranked_by_contribution_and_not_by_value(case):
    contributions = [term.contribution for term in case.reasons]
    assert contributions == sorted(contributions, reverse=True)
    assert case.reasons == ranked_by_contribution(case.scored)[: len(case.reasons)]


def test_a_reason_is_one_of_the_terms_and_not_a_second_computation_of_it(case):
    """Asserted with ``is``: a card cannot show a reason built from another score."""

    for reason in case.reasons:
        assert any(reason is term for term in case.terms)


def test_at_most_three_reasons_come_back(case):
    assert len(case.reasons) == min(CONSTANTS.reasons_returned, len(case.scored))


def test_ranking_by_contribution_survives_renormalisation(case):
    """Every share is the same weight over the same total, so the order cannot move.

    Which reasons a card shows therefore does not change because some *other* term
    was excluded, which is what would happen if reasons were ranked on renormalised
    contribution instead.
    """

    shares = dict(zip(case.scored, renormalise(case.scored), strict=True))
    order = sorted(case.scored, key=lambda term: -(shares[term] * term.value))
    assert [term.code for term in order[: len(case.reasons)]] == [
        term.code for term in case.reasons
    ]


def test_a_warning_is_the_weakest_contributor_and_only_on_its_own_value(case):
    weakest = lowest_contribution(case.scored)
    if weakest.value < CONSTANTS.warning_threshold:
        assert case.warning is weakest
    else:
        assert case.warning is None


def test_the_weakest_contributor_and_the_last_reason_break_ties_the_same_way():
    """``min`` and a descending sort disagree about ties, so one rule is used twice.

    Two terms contributing exactly the same amount: the lowest contributor must be
    the first of them in table order, which is the same tie-break the reason ranking
    applies. Otherwise the warning would fall on whichever of two indistinguishable
    terms the sort left last.
    """

    tied = tuple(
        constraint_term(
            code, 6, ratio(1, 2), PriceFact(payable=grosze(1), ceiling=None)
        )
        if code is TermCode.PRICE
        else constraint_term(
            code, 6, ratio(1, 2), LadderFact(qualification=LadderQualification.OUTSIDE)
        )
        for code in (TermCode.LADDER_QUALIFICATION, TermCode.PRICE)
    )
    assert lowest_contribution(tied) is tied[0]
    assert ranked_by_contribution(tied) == tied


# --- The two producers, and the inputs -------------------------------------------


def test_every_score_carries_both_engine_versions(case):
    assert case.engine_version == ENGINE_VERSION == ENGINE.version
    assert case.pairing_version == "pairing-v1"


def test_the_pairing_version_is_read_off_the_analysis_and_never_carried():
    """A score cannot name a pairing version other than the one it was scored with."""

    result = ENGINE.score(
        snapshot=doubles(ADA, BO, CY, DEE),
        profile=profile(),
        analysis=analysis(version="pairing-v9"),
        now=NOW,
    )
    assert result.pairing_version == "pairing-v9"


def test_the_engine_satisfies_the_protocol():
    assert isinstance(ENGINE, MatchFitEngine)


@pytest.mark.parametrize("field_name", ["second", "microsecond"])
def test_an_instant_that_is_not_rounded_to_the_minute_is_refused(field_name):
    unrounded = NOW.replace(**{field_name: 30})
    with pytest.raises(InvariantViolated, match="not rounded to the minute"):
        ENGINE.score(
            snapshot=doubles(ADA, BO, CY, DEE),
            profile=profile(),
            analysis=analysis(),
            now=unrounded,
        )


def test_the_same_inputs_produce_the_same_score(shape, case):
    _, snapshot, declaration, aim = shape
    again = scored(snapshot, declaration, aim)
    assert (again.fit, again.coverage, again.terms) == (
        case.fit,
        case.coverage,
        case.terms,
    )


def test_only_the_viability_term_depends_on_the_instant_it_is_asked_at(shape, case):
    """``now`` enters the score through **exactly one** term, and which one is the rule.

    *When the match is* and *when you asked* are different questions. Time fit reads
    the match's own start, so the same Tuesday evening scores the same at breakfast
    and at midnight; viability reads the run-up to the join cutoff, which is measured
    from the moment the question is asked and *should* move — a match with an unpaid
    seat and five minutes left is a worse recommendation than the same match a day
    out.

    Asked a year later, every term but viability is the identical object. That is a
    stronger statement than comparing values: a term rebuilt from a different instant
    would compare equal on its value and differ on the payload beside it.
    """

    _, snapshot, declaration, aim = shape
    later = ENGINE.score(
        snapshot=snapshot,
        profile=declaration,
        analysis=aim,
        now=NOW.replace(year=2027, month=1, day=1, hour=6, minute=45),
    )
    unmoved = tuple(
        term for term in case.terms if term.code is not TermCode.MATCH_VIABILITY
    )
    assert (
        tuple(term for term in later.terms if term.code is not TermCode.MATCH_VIABILITY)
        == unmoved
    )
    # A year past every cutoff in the suite, nothing can still be filled: the unpaid
    # part of the roster is worth nothing and the court side is all that is left.
    stale = _term(later, TermCode.MATCH_VIABILITY)
    fresh = _term(case, TermCode.MATCH_VIABILITY)
    assert isinstance(stale, ScoredTerm) and isinstance(fresh, ScoredTerm)
    assert stale.value <= fresh.value


# --- Price reads the payable, and travel never excludes --------------------------


def test_price_reads_the_payable_and_not_the_seat_share():
    """*What the player actually owes after a club card* — asserted, not commented.

    The share is on the snapshot for a card to strike through. Move it and the score
    must not budge; move the payable and it must. A term reading the share would pass
    the first half of this and fail the second.
    """

    declaration = profile(ceiling=2000)
    match = doubles(ADA, BO, CY, DEE)
    louder_share = replace(match, seat_share=grosze(9000))
    assert scored(louder_share, declaration).fit == scored(match, declaration).fit

    cheaper = replace(match, payable=grosze(1500))
    assert scored(cheaper, declaration).fit > scored(match, declaration).fit


def test_price_and_travel_score_zero_rather_than_dropping_out():
    """*Nothing is ever excluded on distance*, and price is a condition not a
    rejection. A match ten times the ceiling and four hours away still scores, still
    carries its weight, and still says what it read."""

    absurd = replace(
        doubles(ADA, BO, CY, DEE, travel_minutes=240),
        seat_share=grosze(50_000),
        payable=grosze(50_000),
    )
    result = scored(absurd, profile(ceiling=1000, radius=10))
    price = _term(result, TermCode.PRICE)
    travel = _term(result, TermCode.TRAVEL)
    assert isinstance(price, ScoredTerm) and price.value == 0
    assert isinstance(travel, ScoredTerm) and travel.value == 0
    assert result.coverage == scored(absurd, profile()).coverage


def _term(result: MatchFitScore, code: TermCode):
    return next(term for term in result.terms if term.code is code)


def test_the_decay_is_full_marks_inside_the_limit_and_floors_at_nothing():
    assert decayed(ratio(0, 1), ratio(1, 1)) == FULL_MARKS
    assert decayed(ratio(1, 2), ratio(1, 1)) == ratio(1, 2)
    assert decayed(ratio(1, 1), ratio(1, 1)) == NO_MARKS
    assert decayed(ratio(9, 1), ratio(1, 1)) == NO_MARKS
    # A limit with no tolerance at all: anything past it scores nothing, and
    # nothing divides by zero.
    assert decayed(ratio(0, 1), ratio(0, 1)) == FULL_MARKS
    assert decayed(ratio(1, 100), ratio(0, 1)) == NO_MARKS


def test_a_decay_from_inside_the_limit_is_a_caller_bug():
    """The clamp belongs at the call site, so a cheap match cannot score above
    full marks by being *negatively* beyond its ceiling.

    Built through ``Ratio(...)`` rather than ``ratio(...)``, because the kernel's
    constructor already refuses a negative numerator — and the brand **erases**, so
    the one path to a negative here is a caller assembling a ``Fraction`` itself.
    That is exactly the path this guard is for, and asserting it through the
    constructor that cannot produce one would be testing the kernel instead.
    """

    with pytest.raises(InvariantViolated, match="inside the limit"):
        decayed(Ratio(Fraction(-1, 2)), ratio(1, 1))


# --- Time fit reads a clock face, and the clock face is the club's ---------------


def _time(snapshot: MatchSnapshot, declaration: PlayerProfile) -> ScoredTerm:
    term = next(
        item
        for item in scored(snapshot, declaration).terms
        if item.code is TermCode.TIME_FIT
    )
    assert isinstance(term, ScoredTerm)
    return term


@pytest.mark.parametrize("name, snapshot, declaration, aim", CASES, ids=IDS)
def test_the_time_term_reads_both_halves_through_the_kernel(
    name, snapshot, declaration, aim
):
    """*Never by ad-hoc date arithmetic*, as something a test can hold the term to.

    The payload's weekday and minute are asserted to be exactly what the kernel's
    two readers return for this match's start in this club's zone. An engine that
    computed either half itself would agree here on most days and disagree on the
    two hours either side of a local midnight and twice a year, which is precisely
    the class of bug nobody notices from a passing suite.
    """

    fact = _time(snapshot, declaration).fact
    assert isinstance(fact, TimeFact)
    zone = snapshot.club.zone
    assert fact.weekday.value == local_iso_weekday(snapshot.start, zone)
    assert fact.minute == local_minute_of_day(snapshot.start, zone)


def test_a_match_after_midnight_utc_is_on_the_local_day_and_not_the_utc_one():
    """22:30 UTC on a Sunday is already **Monday** in Warsaw.

    The case that makes the conversion load-bearing rather than decorative: a term
    reading the weekday off the instant would say Sunday, and somebody who declared
    Sundays would be shown a match starting at half past midnight on Monday. Both
    directions are asserted, so a mutation swapping the zone for UTC fails on the
    declaration it satisfies as well as on the one it breaches.
    """

    after_midnight = doubles(ADA, BO, CY, DEE, start=starting(day=7, hour=0, minute=30))
    assert after_midnight.start.isoweekday() == 7
    assert _time(after_midnight, profile(days=frozenset({Weekday.MONDAY}))).value == 1
    assert (
        _time(after_midnight, profile(days=frozenset({Weekday.SUNDAY}))).value
        == CONSTANTS.time_outside
    )


def test_the_clock_face_survives_a_daylight_saving_change():
    """Poland observes DST, so the offset the conversion uses is not a constant.

    01:30 UTC on 29 March 2026 is 03:30 in Warsaw, because the clocks went forward
    an hour earlier that morning; read with the winter offset it would be 02:30, an
    hour that does not exist that day. A declaration of 03:00–06:00 is satisfied and
    one of 02:00–03:00 is not, which is the same fact asserted from both sides.
    """

    spring_forward = doubles(
        ADA,
        BO,
        CY,
        DEE,
        start=instant(datetime(2026, 3, 29, 1, 30, tzinfo=timezone.utc)),
    )
    assert local_minute_of_day(spring_forward.start, WARSAW) == 3 * 60 + 30
    assert _time(spring_forward, profile(hours=(window(3, 6),))).value == 1
    assert (
        _time(spring_forward, profile(hours=(window(2, 3),))).value
        == CONSTANTS.time_outside
    )


def test_one_match_at_two_clubs_in_different_zones_scores_differently():
    """The zone is read off the *club*, which is what makes it a club fact.

    One instant, one declaration, two clubs: 20:30 in Warsaw is 19:30 in London, and
    a player who declared 19:00–20:00 can play at one of them. Nothing else moves.
    """

    declaration = profile(hours=(window(19, 20),))
    at_seven_thirty_in_london = doubles(
        ADA, BO, CY, DEE, start=starting(hour=20, minute=30), zone=Zone("Europe/London")
    )
    at_eight_thirty_in_warsaw = replace(
        at_seven_thirty_in_london,
        club=replace(at_seven_thirty_in_london.club, zone=WARSAW),
    )
    assert _time(at_seven_thirty_in_london, declaration).value == 1
    assert _time(at_eight_thirty_in_warsaw, declaration).value == CONSTANTS.time_outside


def test_a_match_outside_the_declaration_ranks_lower_and_is_never_hidden():
    """*Matches outside them rank lower without being hidden*, as arithmetic.

    A declaration is a soft filter here, exactly as price and distance are: the term
    scores above nothing and always runs, so a Saturday morning match reaches
    somebody who declared weekday evenings as a card they can overrule rather than
    as an absence they cannot argue with.
    """

    weekday_evenings = profile(
        days=frozenset({Weekday.MONDAY, Weekday.TUESDAY}), hours=(window(18, 22),)
    )
    outside = _time(doubles(ADA, BO, CY, DEE, start=starting(day=5)), weekday_evenings)
    assert 0 < outside.value < 1
    assert outside.kind is TermKind.CONSTRAINT
    assert isinstance(outside, ScoredTerm)


def test_declaring_only_one_half_leaves_the_other_unconstrained():
    """Days and hours are two declarations, and each silence is its own *no limit*.

    A player who named days and no hours has no hour problem, and one who named
    hours and no days has no day problem. Reading either silence as *nothing works*
    is the mistake ``PlayerProfile`` refuses an empty set for.
    """

    tuesday_seven_in_the_morning = doubles(
        ADA, BO, CY, DEE, start=starting(hour=7, minute=0)
    )
    assert _time(tuesday_seven_in_the_morning, profile()).value == 1
    days_only = profile(days=frozenset({Weekday.TUESDAY}))
    hours_only = profile(hours=(window(6, 9),))
    assert _time(tuesday_seven_in_the_morning, days_only).value == 1
    assert _time(tuesday_seven_in_the_morning, hours_only).value == 1
    both = profile(days=frozenset({Weekday.TUESDAY}), hours=(window(18, 22),))
    assert _time(tuesday_seven_in_the_morning, both).value == CONSTANTS.time_outside


def test_which_half_failed_is_reported_even_though_it_does_not_move_the_score():
    """One value for both halves, and a payload that can still tell them apart.

    The score says *you cannot play then*; the payload says whether it was the day
    or the hour. That is what lets a client write the true sentence without the
    engine having to encode two constants and an ordering between them that no
    measurement here could settle.
    """

    declaration = profile(days=frozenset({Weekday.TUESDAY}), hours=(window(18, 22),))
    wrong_hour = _time(
        doubles(ADA, BO, CY, DEE, start=starting(hour=7, minute=0)), declaration
    ).fact
    saturday = doubles(ADA, BO, CY, DEE, start=starting(day=5))
    wrong_day = _time(saturday, declaration).fact
    assert isinstance(wrong_hour, TimeFact) and isinstance(wrong_day, TimeFact)
    assert wrong_hour.on_a_declared_day and not wrong_hour.inside_a_declared_window
    assert wrong_day.inside_a_declared_window and not wrong_day.on_a_declared_day


# --- Viability: the evidence term that cannot go missing -------------------------


def _viability(result: MatchFitScore) -> ScoredTerm:
    term = _term(result, TermCode.MATCH_VIABILITY)
    assert isinstance(term, ScoredTerm)
    return term


def test_viability_is_evidence_and_always_runs(case):
    """**Evidence-typed but always computable**, which is the whole of its job.

    Evidence, because whether a match will be played is something the platform
    *observes* and never something the player declared — reading it as a constraint
    would make a match with no court held score full marks for having no limit on it.

    Always computable, because every match has a phase, a court hold, a seat count
    and a cutoff. So it is the one evidence term that is never excluded, and it is
    what makes *absence never flatters* true of a **ranking**: without it, a court
    nobody has joined is scored on constraints alone and satisfies all of them.
    """

    term = _viability(case)
    assert term.kind is TermKind.EVIDENCE
    assert term.code not in {excluded.code for excluded in case.excluded}


def test_viability_never_lowers_coverage(shape, case):
    """*It is never excluded and never reduces Coverage*, measured rather than said.

    The same match with every viability fact at its worst has exactly the coverage of
    the same match at its best: the term ran in both, so the weight is in both
    numerators. Coverage reports on what the platform **looked at**, never on what it
    found.
    """

    _, snapshot, declaration, aim = shape
    hopeless = scored(
        replace(
            snapshot,
            hold=CourtHold.NONE,
            club=replace(snapshot.club, crowding=ratio(1, 1)),
            join_cutoff=shifted(NOW, minutes(-1)),
        ),
        declaration,
        aim,
    )
    assert hopeless.coverage == case.coverage
    assert _viability(hopeless).value <= _viability(case).value


def test_viability_reads_the_four_facts_and_reports_them(shape, case):
    """The payload is the four quantities the term was scored from, not a summary.

    Read back off the snapshot, so a term that scored one match and reported another
    — the shape a refactor produces when a helper is handed the wrong argument —
    fails here rather than on a card nobody is checking.
    """

    _, snapshot, _, _ = shape
    fact = _viability(case).fact
    assert isinstance(fact, ViabilityFact)
    assert (fact.paid_seats, fact.sold_seats) == (
        snapshot.paid_seats,
        snapshot.sold_seats,
    )
    assert fact.hold is snapshot.hold
    assert fact.crowding == snapshot.club.crowding
    assert fact.minutes_to_cutoff == (snapshot.join_cutoff - NOW).total_seconds() // 60


def test_viability_is_the_chance_of_people_times_the_chance_of_a_court(shape, case):
    """The arithmetic, written out independently of the engine that ran it.

    An oracle rather than a restatement: the two halves are spelled here from the
    sentence the term's docstring makes — *what is already committed, plus what might
    still be got, discounted* — and the two agree only if both are right. A term that
    blended the halves instead of multiplying them, or that discounted the paid part
    instead of the unpaid one, disagrees on the very first case.
    """

    _, snapshot, _, _ = shape
    paid = ratio(snapshot.paid_seats, snapshot.sold_seats)
    left = (snapshot.join_cutoff - NOW).total_seconds() // 60
    window = CONSTANTS.fill_window
    reachable = ratio(max(0, min(int(left), window)), 1) / window
    people = paid + (1 - paid) * CONSTANTS.seat_fill_ceiling * reachable
    held = CONSTANTS.hold_confidence[snapshot.hold]
    court = held + (1 - held) * (1 - snapshot.club.crowding)
    assert _viability(case).value == people * court


def test_a_full_match_with_a_booked_court_is_the_only_way_to_reach_full_marks():
    """Both halves at one, and nothing else gets there.

    Worth pinning because it is the claim a card makes: *this match is happening*.
    Every seat paid and a court booked is the only state that earns it — a held seat
    does not, because attendance is exactly what a held seat has not committed to.
    """

    certain = doubles(ADA, BO, CY, DEE, hold=CourtHold.HARD, crowding=100)
    assert _viability(scored(certain, profile())).value == 1

    for lesser in (
        doubles(ADA, BO, CY, DEE, hold=CourtHold.SOFT, crowding=100),
        doubles(
            ADA,
            BO,
            CY,
            DEE,
            states=(SeatState.PAID, SeatState.PAID, SeatState.PAID, SeatState.HELD),
        ),
        doubles(ADA, BO, CY, None),
    ):
        assert _viability(scored(lesser, profile())).value < 1


def test_a_court_that_is_booked_is_untouched_by_how_busy_the_club_is():
    """The one flat case, and it is a claim rather than an artefact.

    A hard hold is a booking: the club has committed that court, so its being busy
    cannot take it away. An arithmetic that let crowding bite a booked court would be
    charging the match twice for a risk it has already retired.
    """

    scores = {
        crowded: _viability(
            scored(doubles(ADA, BO, CY, DEE, crowding=crowded), profile())
        ).value
        for crowded in (0, 50, 100)
    }
    assert len(set(scores.values())) == 1

    unheld = {
        crowded: _viability(
            scored(
                doubles(ADA, BO, CY, DEE, hold=CourtHold.NONE, crowding=crowded),
                profile(),
            )
        ).value
        for crowded in (0, 50, 100)
    }
    assert len(set(unheld.values())) == 3


def test_a_match_past_its_cutoff_is_scored_and_not_refused():
    """Past the cutoff there is nothing left to fill, and the floor answers.

    A match this old should have been filtered out before an engine saw it, so this
    is not a state to model — it is the state the arithmetic must not *explode* in,
    since a caller's filtering bug should produce a bad score and a payload saying
    why, rather than a stack trace in a home list.
    """

    stale = doubles(ADA, None, None, None, cutoff=shifted(NOW, minutes(-600)))
    term = _viability(scored(stale, profile()))
    fact = term.fact
    assert isinstance(fact, ViabilityFact)
    assert fact.minutes_to_cutoff == -600
    assert term.value == ratio(1, 4)


def test_a_match_in_a_phase_nobody_can_join_never_reaches_a_term(shape):
    """The hard filter, enforced where an engine could otherwise be handed one.

    A cancelled match ranked last is still a cancelled match in a home list, so the
    snapshot refuses it outright and no term has to encode *is this joinable at all*
    as a low number.
    """

    _, snapshot, _, _ = shape
    for phase in (MatchPhase.LOCKED, MatchPhase.CANCELLED):
        with pytest.raises(InvariantViolated, match="only a forming match"):
            replace(snapshot, phase=phase)


# --- The two terms that read the pairing analysis --------------------------------


def _overlap(result: MatchFitScore):
    return _term(result, TermCode.SKILL_OVERLAP)


def _balance(result: MatchFitScore):
    return _term(result, TermCode.PREDICTED_BALANCE)


def test_both_pairing_terms_are_evidence_and_never_constraints(case):
    """The reclassification, as the property that makes it structural.

    ``TermKind`` is not a label somebody set: it is which of ``core``'s two builders
    was called, and only one of them can produce an exclusion. So *skill overlap is
    evidence* is checkable on every shape, including the ones where it happens to
    score full marks — which is exactly where a constraint would be indistinguishable
    from it by value alone.
    """

    for code in (TermCode.SKILL_OVERLAP, TermCode.PREDICTED_BALANCE):
        assert _term(case, code).kind is TermKind.EVIDENCE


def test_a_match_with_nothing_to_be_aimed_at_excludes_the_overlap_term():
    """**The single reclassification the whole spec turns on**, and its counterfactual.

    A court nobody has joined has no seat target and no band, so there is nothing for
    the player's Level to overlap with. The term is excluded and 24 points leave the
    denominator.

    The counterfactual is written out beside it because it is the actual regression:
    scoring the term against the *player's own Level* is a distance of zero and
    therefore full marks, on the largest weight in the table, for the match the
    platform knows least about. Asserted as an inequality against that alternative
    rather than described — the excluded score must not be the one full marks would
    have produced.
    """

    empty = doubles(None, None, None, None, viewer=ADA)
    excluded = scored(empty, profile(), UNAIMED)
    assert isinstance(_overlap(excluded), ExcludedTerm)
    assert not hasattr(_overlap(excluded), "value")
    assert excluded.coverage == 100 - sum(
        CONSTANTS.weights[code]
        for code in (
            TermCode.SKILL_OVERLAP,
            TermCode.PREDICTED_BALANCE,
            TermCode.GROUP_RELIABILITY,
            TermCode.FAMILIARITY,
        )
    )

    # The source design's answer: aim the match at the player who is looking at it.
    flattered = scored(empty, profile(), analysis(band=300))
    assert _overlap(flattered).value == FULL_MARKS
    assert flattered.coverage > excluded.coverage
    assert flattered.fit > excluded.fit


def test_a_viewer_the_platform_cannot_place_on_this_scale_excludes_it_too():
    """The other half of the same silence, and it is not a bad match.

    A player rated at tennis and never at padel is browsing padel. The match is well
    aimed; half of the comparison simply does not exist, and *"we have never rated
    you"* is not *"this is perfect for you"*. Predicted balance is untouched, because
    how even a match will be is a fact about the match: the two are separate terms
    precisely so one silence does not take the other with it.
    """

    stranger = scored(doubles(ADA, BO, CY, DEE, viewer=unrated("newcomer")), profile())
    assert isinstance(_overlap(stranger), ExcludedTerm)
    assert isinstance(_balance(stranger), ScoredTerm)
    assert (
        stranger.coverage
        == scored(doubles(ADA, BO, CY, DEE), profile()).coverage
        - CONSTANTS.weights[TermCode.SKILL_OVERLAP]
    )


def test_the_seat_target_answers_before_the_band_does():
    """*Exact where the pairing engine could be exact, blunt otherwise.*

    Both fields answering is the shape a match one seat from full is in, and the term
    reads the seat target — which is the acceptance criterion's *"from the Seat target
    where exactly one seat is open"*, expressed as the pairing engine's own condition
    for answering rather than as a seat count this engine repeats.

    ``band_half_width`` is what says which of the two it read, and it is asserted in
    both directions: absent for the exact answer, and the band's own width for the
    fallback. A term that read the band while reporting no width would be a payload
    disagreeing with the score beside it.
    """

    match = doubles(ADA, BO, CY, None)
    exact = _overlap(scored(match, profile(), analysis(band=340, seat_target=300)))
    blunt = _overlap(scored(match, profile(), analysis(band=340)))
    assert isinstance(exact, ScoredTerm) and isinstance(blunt, ScoredTerm)
    assert isinstance(exact.fact, SkillOverlapFact)
    assert isinstance(blunt.fact, SkillOverlapFact)
    assert exact.fact.target == level(300) and exact.fact.band_half_width is None
    assert blunt.fact.target == level(340)
    assert blunt.fact.band_half_width == ratio(50, 100)
    assert exact.value > blunt.value


def test_the_target_is_read_off_the_analysis_and_never_off_the_snapshot():
    """*The analysis is an input value, never a collaborator* — as a measurement.

    Move a seated player's Level and the term does not budge, because the target is
    the pairing engine's conclusion and this engine does not hold the arithmetic that
    produces one. Move the *viewer's* Level and it does, because that half is the
    snapshot's. An engine that quietly re-derived a target from the roster would move
    on the first, and would then be scoring a match against a pairing nobody was
    shown — the exact failure the import fence exists to prevent, in the one shape a
    contract cannot see.
    """

    aim = analysis(estimate=90, band=300)
    match = doubles(ADA, BO, CY, DEE, viewer=ADA)
    reseated = replace(
        match,
        seats=(
            match.seats[0],
            match.seats[1],
            match.seats[2],
            replace(match.seats[3], occupant=skill("dee", 480, 60)),
        ),
    )
    assert _overlap(scored(reseated, profile(), aim)) == _overlap(
        scored(match, profile(), aim)
    )

    stronger = doubles(ADA, BO, CY, DEE, viewer=skill("ada", 380, 20))
    assert (
        _overlap(scored(stronger, profile(), aim)).value
        < _overlap(scored(match, profile(), aim)).value
    )


def test_the_overlap_term_is_symmetric_about_the_target():
    """A Level too strong and a Level too weak are the same distance from the match.

    One value for both directions, deliberately, because an ordering between them is
    a claim no measurement here could settle — the same argument ``time_outside``
    makes for the wrong day and the wrong hour. What is *not* lost is which direction
    it was: both Levels are on the payload, so a client says *above* or *below*
    without the score having encoded it.
    """

    aim = analysis(estimate=90, band=300)
    weaker = doubles(skill("ada", 260, 20), BO, CY, DEE)
    stronger = doubles(skill("ada", 340, 20), BO, CY, DEE)
    below = _overlap(scored(weaker, profile(), aim))
    above = _overlap(scored(stronger, profile(), aim))
    assert isinstance(below, ScoredTerm) and isinstance(above, ScoredTerm)
    assert isinstance(below.fact, SkillOverlapFact)
    assert isinstance(above.fact, SkillOverlapFact)
    assert below.value == above.value
    assert below.fact.distance == above.fact.distance == ratio(40, 100)
    assert below.fact.level < below.fact.target < above.fact.level


def test_the_balance_term_is_the_estimate_and_has_no_curve_of_its_own():
    """**No constant, and that is the claim.**

    A balance percentage is already a mark out of a hundred about the match, so
    fitting a curve to it would be a second opinion about what one means — and the
    first is a product commitment the pairing engine's ``gap_coefficient`` was solved
    from. The term's value is therefore the estimate over a hundred at every point of
    the scale, floor included, which is checkable without naming a single constant of
    this engine's.
    """

    match = doubles(ADA, BO, CY, DEE)
    for estimate in (35, 50, 78, 92, 100):
        term = _balance(scored(match, profile(), analysis(estimate=estimate)))
        assert isinstance(term, ScoredTerm)
        assert term.value == ratio(estimate, 100)
        assert whole_percent(term.value) == estimate


def test_a_forecast_unfit_to_print_still_ranks_and_only_a_missing_one_is_excluded():
    """*Suppression is presentation.* Excluded on **absence**, never on uncertainty.

    The same estimate at a margin narrow enough to print and at one wide enough that
    a card will show nothing scores identically — because the best estimate remains
    the best estimate when it is unfit to print, and withholding it from the ranking
    would make an uncertain match unrankable rather than honest.

    The margin is not charged a second time either: the estimate is the *expected
    absolute* gap, so uncertainty has already made it worse on the way in. What
    excludes the term is having no forecast at all.
    """

    match = doubles(ADA, BO, CY, DEE)
    unsure = scored(
        match,
        profile(),
        analysis(estimate=78, margin=40, certainty=Certainty.LOW, band=300),
    )
    sure = scored(
        match,
        profile(),
        analysis(estimate=78, margin=2, certainty=Certainty.HIGH, band=300),
    )
    assert (unsure.fit, unsure.coverage) == (sure.fit, sure.coverage)
    assert _balance(unsure).value == _balance(sure).value

    missing = scored(match, profile(), analysis(band=300))
    assert isinstance(_balance(missing), ExcludedTerm)
    assert (
        missing.coverage
        == sure.coverage - CONSTANTS.weights[TermCode.PREDICTED_BALANCE]
    )


# --- The value object's own guards ----------------------------------------------


def _some_term(code: TermCode = TermCode.PRICE, value=FULL_MARKS) -> ScoredTerm:
    return constraint_term(code, 6, value, PriceFact(payable=grosze(1), ceiling=None))


def test_a_score_over_no_terms_at_all_is_refused():
    with pytest.raises(InvariantViolated, match="no terms at all"):
        MatchFitScore(
            fit=100,
            coverage=100,
            terms=(),
            reasons=(),
            warning=None,
            engine_version=ENGINE_VERSION,
            pairing_version="pairing-v1",
        )


def test_a_score_where_nothing_ran_is_refused():
    """A weighted average over no weight is a division by zero, not a low score."""

    with pytest.raises(InvariantViolated, match="no term that ran"):
        MatchFitScore(
            fit=0,
            coverage=0,
            terms=(ExcludedTerm(code=TermCode.FAMILIARITY, weight=3),),
            reasons=(),
            warning=None,
            engine_version=ENGINE_VERSION,
            pairing_version="pairing-v1",
        )


def test_the_same_term_twice_is_refused():
    with pytest.raises(InvariantViolated, match="scored twice"):
        MatchFitScore(
            fit=100,
            coverage=100,
            terms=(_some_term(), _some_term()),
            reasons=(),
            warning=None,
            engine_version=ENGINE_VERSION,
            pairing_version="pairing-v1",
        )


@pytest.mark.parametrize("fit, coverage", [(101, 100), (-1, 100), (100, 101)])
def test_a_figure_outside_nought_to_a_hundred_is_refused(fit, coverage):
    with pytest.raises(InvariantViolated, match="outside 0..100"):
        MatchFitScore(
            fit=fit,
            coverage=coverage,
            terms=(_some_term(),),
            reasons=(),
            warning=None,
            engine_version=ENGINE_VERSION,
            pairing_version="pairing-v1",
        )


def test_a_term_value_outside_its_range_is_refused():
    with pytest.raises(InvariantViolated, match="outside 0..1"):
        _some_term(value=ratio(3, 2))
    with pytest.raises(InvariantViolated, match="outside 0..1"):
        Observed(value=ratio(3, 2), fact=FamiliarityFact(new_faces=1, others=1))


def test_a_term_carrying_another_terms_payload_is_refused():
    """The code and the payload's kind are the same machine key spelled twice."""

    with pytest.raises(InvariantViolated, match="carrying a travel payload"):
        constraint_term(
            TermCode.PRICE, 6, FULL_MARKS, TravelFact(minutes=minutes(0), radius=None)
        )


def test_a_term_with_no_weight_is_refused():
    with pytest.raises(InvariantViolated, match="weight 0"):
        ExcludedTerm(code=TermCode.FAMILIARITY, weight=0)
    with pytest.raises(InvariantViolated, match="weight 0"):
        constraint_term(
            TermCode.PRICE, 0, FULL_MARKS, PriceFact(payable=grosze(1), ceiling=None)
        )


def test_the_score_is_immutable(case):
    with pytest.raises(FrozenInstanceError):
        case.fit = 1


# --- The constants ---------------------------------------------------------------


def test_the_declared_weights_sum_to_a_hundred_and_nothing_is_pending():
    """*The weights sum to 100*, now in the **unqualified** form.

    ``PENDING_WEIGHTS`` existed to make *"the table is incomplete"* an arithmetic
    statement rather than a comment, and completing the table was exactly the diff it
    described: two lines moved from one mapping to the other. Both the mapping and
    the guard that reads it survive it being empty, so an eleventh term declares its
    debt the same way rather than by lowering every Coverage figure in silence.
    """

    assert sum(CONSTANTS.weights.values()) + sum(PENDING_WEIGHTS.values()) == 100
    assert WEIGHT_TOTAL == 100
    assert dict(PENDING_WEIGHTS) == {}
    assert sum(CONSTANTS.weights.values()) == 100
    assert len(CONSTANTS.weights) == len(TermCode) == 10


def test_a_table_that_does_not_sum_to_a_hundred_is_refused():
    with pytest.raises(InvariantViolated, match="not 100"):
        MatchFitConstants(weights={TermCode.PRICE: 6})


def test_a_term_the_vocabulary_names_and_the_table_does_not_weight_is_refused():
    with pytest.raises(InvariantViolated, match="the vocabulary names"):
        MatchFitConstants(
            weights={
                code: weight
                for code, weight in (
                    (TermCode.SKILL_OVERLAP, 24),
                    (TermCode.PREDICTED_BALANCE, 14),
                    (TermCode.TIME_FIT, 12),
                    (TermCode.MATCH_VIABILITY, 12),
                    (TermCode.GROUP_RELIABILITY, 11),
                    (TermCode.TRAVEL, 8),
                    (TermCode.LADDER_QUALIFICATION, 6),
                    (TermCode.PRICE, 6),
                    (TermCode.MATCH_TYPE, 7),
                )
            }
        )


def test_a_hold_ladder_that_falls_is_refused():
    """*A firmer hold never makes a match less likely to be played*, at the retune.

    Checked when the constants are built and against ``HOLD_LADDER`` — the
    vocabulary's order — so a retune that made a soft hold worth more than a booked
    court fails at import rather than on one home screen. This is what makes the
    monotonicity property true under **any** retune rather than under this one.
    """

    rungs = [CONSTANTS.hold_confidence[rung] for rung in HOLD_LADDER]
    assert rungs == sorted(rungs)
    with pytest.raises(InvariantViolated, match="hold ladder falls"):
        MatchFitConstants(
            hold_confidence={
                CourtHold.NONE: ratio(0, 1),
                CourtHold.SOFT: ratio(90, 100),
                CourtHold.HARD: ratio(40, 100),
            }
        )


def test_a_hold_the_vocabulary_names_and_the_ladder_does_not_score_is_refused():
    """A rung with no confidence behind it is a hold the term cannot read at all,
    and the failure would be a ``KeyError`` three frames down from the retune."""

    with pytest.raises(InvariantViolated, match="the vocabulary names"):
        MatchFitConstants(
            hold_confidence={
                CourtHold.NONE: ratio(0, 1),
                CourtHold.HARD: ratio(100, 100),
            }
        )


@pytest.mark.parametrize("chance", [Ratio(Fraction(-1, 10)), ratio(11, 10)])
def test_a_hold_confidence_outside_nought_to_one_is_refused(chance):
    """It is a probability, so it is bounded like one — and a rung above one would
    push a viability above full marks, which the term's own value object refuses one
    frame later and with a worse message."""

    with pytest.raises(InvariantViolated, match="hold outside"):
        MatchFitConstants(
            hold_confidence={
                CourtHold.NONE: chance,
                CourtHold.SOFT: chance,
                CourtHold.HARD: chance,
            }
        )


def test_a_fill_window_of_nothing_is_refused():
    """A window of zero is a cliff at the cutoff rather than a run-up to it, and it
    would make *how long is left* a fact the term reads and never uses."""

    with pytest.raises(InvariantViolated, match="fill window"):
        MatchFitConstants(fill_window=minutes(0))


@pytest.mark.parametrize("mismatch", [ratio(1, 1), ratio(3, 2)])
def test_a_mismatch_worth_full_marks_or_more_is_refused(mismatch):
    """At full marks the term is not a constraint any more: a friendly and a rated
    match would score identically for somebody who asked for one of them.

    All four of them, because the guard is a loop over a written-out list and a value
    left off it is a constant nothing checks — which is exactly what a mutation run
    found the first time this list was one short.

    The seat fill ceiling is in the same family and is the one that matters most: at
    full marks an unpaid seat would be worth exactly as much as a paid one given
    enough time, so a match nobody has joined would score like a full one and the
    term written to close *absence never flatters* would have reopened it.
    """

    with pytest.raises(InvariantViolated, match="not below full marks"):
        MatchFitConstants(time_outside=mismatch)
    with pytest.raises(InvariantViolated, match="not below full marks"):
        MatchFitConstants(match_type_mismatch=mismatch)
    with pytest.raises(InvariantViolated, match="not below full marks"):
        MatchFitConstants(ladder_outside=mismatch)
    with pytest.raises(InvariantViolated, match="not below full marks"):
        MatchFitConstants(seat_fill_ceiling=mismatch)


def test_a_span_of_nothing_is_refused():
    with pytest.raises(InvariantViolated, match="price span"):
        MatchFitConstants(price_decay_span=ratio(0, 1))
    with pytest.raises(InvariantViolated, match="overlap span"):
        MatchFitConstants(overlap_span=ratio(0, 1))


def test_the_time_and_travel_weight_is_now_two_terms_that_move_independently():
    """The split the spec asks for, asserted as the sum it was split from.

    The source document labelled one term *"Time and travel"* and computed only the
    travel half. The 20 points it held are now 12 and 8, two terms with their own
    curves and their own falsifying measurements — and the table still sums to 100,
    which the constants refuse to be built without.

    **Where the 20 comes from is worth saying plainly**: the source document is not
    in this repository. The figure is the one this repo's own table committed to,
    when ``time_fit`` 12 was written into ``PENDING_WEIGHTS`` beside travel's 8, and
    that is what this pins — a later retune is free to move either, and not free to
    move them without this test saying so.
    """

    assert CONSTANTS.weights[TermCode.TIME_FIT] == 12
    assert CONSTANTS.weights[TermCode.TRAVEL] == 8
    split = CONSTANTS.weights[TermCode.TIME_FIT] + CONSTANTS.weights[TermCode.TRAVEL]
    assert split == 20
    assert "time_fit" not in PENDING_WEIGHTS
    declared = sum(CONSTANTS.weights.values())
    assert declared + sum(PENDING_WEIGHTS.values()) == WEIGHT_TOTAL


def test_when_you_can_play_is_the_strictest_of_the_three_declarations():
    """The ordering the three mismatch constants encode, so a retune cannot invert it.

    A match outside your ladder is the right kind of evening that does not count; a
    friendly offered to somebody who asked for counted matches is the wrong kind of
    evening; a 07:00 match offered to somebody who plays after work is an evening
    they are at work for. Two tenths, three tenths, a half — and a retune is free to
    move all three and not free to reorder them without saying so here.
    """

    assert CONSTANTS.time_outside < CONSTANTS.match_type_mismatch
    assert CONSTANTS.match_type_mismatch < CONSTANTS.ladder_outside
    assert CONSTANTS.time_outside > 0


def test_a_ladder_mismatch_is_milder_than_a_match_type_mismatch():
    """The ordering the two constants encode, so a retune cannot silently invert it.

    A match outside your ladder is the right kind of evening that does not count; a
    friendly offered to somebody who asked for counted matches is the wrong kind of
    evening. A retune is free to move both numbers and not free to swap them without
    saying so here.
    """

    assert CONSTANTS.ladder_outside > CONSTANTS.match_type_mismatch


def test_every_constant_carries_the_measurement_that_would_falsify_it():
    """A constant with no falsifying measurement is a preference wearing a
    number's clothes, and retuning it is taste rather than science."""

    source = _parsed(MATCHFIT / "v1" / "constants.py")
    declared = next(
        node
        for node in ast.walk(source)
        if isinstance(node, ast.ClassDef) and node.name == "MatchFitConstants"
    )
    body = declared.body
    unfalsifiable = []
    for index, node in enumerate(body):
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        following = body[index + 1] if index + 1 < len(body) else None
        note = (
            following.value.value
            if isinstance(following, ast.Expr)
            and isinstance(following.value, ast.Constant)
            and isinstance(following.value.value, str)
            else ""
        )
        if "Falsified by:" not in note:
            unfalsifiable.append(node.target.id)
    assert unfalsifiable == [], unfalsifiable
    assert len([node for node in body if isinstance(node, ast.AnnAssign)]) == 12, (
        "the constant count moved — read the new one's falsifying note first"
    )


# --- Gates over the source, for the claims a runtime test cannot make ------------


def _modules_of(package: Path) -> list[Path]:
    return sorted(package.rglob("*.py"))


def _parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_the_one_rounding_rule_agrees_with_the_kernels(case):
    """The rounding **is** the kernel's now (#88), and this pins the scaling.

    It used to mirror a restated copy against the kernel's rule. The copy is gone —
    ``whole_percent`` delegates — so what is left to get wrong is the part this
    function still owns: multiplying by a hundred before rounding rather than after,
    which is the difference between 79 and 0 and is not otherwise asserted anywhere.

    Routed through the kernel's ``apply_fraction`` rather than its rounding directly,
    because a hundred grosze *is* a hundred percent and that spelling keeps the test
    honest even if the delegation is later inlined.
    """

    for value in (
        weighted_value(case.scored),
        measured_share(case.terms),
        ratio(1, 2),
        ratio(1, 200),
        ratio(3, 8),
        ratio(1, 8),
    ):
        assert whole_percent(value) == apply_fraction(grosze(100), value)


def test_the_rounding_is_half_away_from_zero_and_not_half_to_even():
    """78,5 and 79,5 must round the same way, or two neighbouring scores are
    rounded in opposite directions for no reason a player could be told."""

    assert whole_percent(ratio(785, 1000)) == 79
    assert whole_percent(ratio(795, 1000)) == 80
    assert round(78.5) == 78 and round(79.5) == 80


def test_no_float_appears_anywhere_in_the_engine():
    """The whole engine is exact until ``whole_percent``, which returns an ``int``.

    A term value is a ``Ratio``, a weight is an ``int``, and the weighted average of
    those is a rational — so there is no crossing into floating point at all here, not
    even a single one. That is a stronger claim than the pairing engine can make, and
    it is only true while nobody writes a ``float(...)`` or a decimal literal.
    """

    walked = _modules_of(MATCHFIT) + [FIT]
    crossings = [
        f"{path.relative_to(ROOT)}:{node.lineno}"
        for path in walked
        for node in ast.walk(_parsed(path))
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "float"
        )
        or (isinstance(node, ast.Constant) and isinstance(node.value, float))
    ]
    assert len(walked) >= 5, walked
    assert crossings == [], crossings


def test_the_score_carries_no_display_text():
    """*Numbers and machine codes, never words*, as something the source can be
    held to.

    Every field in the output vocabulary is a number, a bool, an exact ratio or an
    enum — with exactly three exceptions, all of them written out: the two engine
    versions, which are identifiers, and each payload's ``kind``, which is a
    ``Literal`` and is the machine key itself. A formatted price, a rendered Level or
    a sentence would show up here as a new ``str`` field. A **Level** is the case
    this most easily loses: ``SkillOverlapFact`` carries two of them, and both are
    exact ratios rather than the *"3,00"* a card prints.
    """

    source = _parsed(FIT)
    fields = [
        (f"{holder.name}.{node.target.id}", ast.unparse(node.annotation))
        for holder in ast.walk(source)
        if isinstance(holder, ast.ClassDef)
        for node in holder.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    ]
    assert sorted(name for name, kind in fields if kind == "str") == [
        "MatchFitScore.engine_version",
        "MatchFitScore.pairing_version",
    ]
    assert sorted(name for name, kind in fields if kind.startswith("Literal[")) == [
        "BalanceFact.kind",
        "FamiliarityFact.kind",
        "LadderFact.kind",
        "MatchTypeFact.kind",
        "PriceFact.kind",
        "ReliabilityFact.kind",
        "SkillOverlapFact.kind",
        "TimeFact.kind",
        "TravelFact.kind",
        "ViabilityFact.kind",
    ]
    assert len(fields) == 52, [name for name, _ in fields]


def test_no_match_fit_suite_reaches_for_the_pairing_engine():
    """*Two seams and no third.*

    Match Fit takes the analysis as a value, so its suites build one by hand and
    there is no integration seam between the two engines. A suite that imported the
    pairing engine would turn every assertion here into an assertion about both, and
    a retune of the pairing constants would start breaking Match Fit's baseline.
    ``.importlinter`` fences the production packages; this fences the tests, which no
    contract covers.
    """

    walked = sorted(Path(__file__).parent.glob("test_matchfit_*.py")) + [
        Path(__file__).parent / "matchmaking_snapshots.py"
    ]
    offenders = [
        f"{path.name}:{node.lineno}: {name}"
        for path in walked
        for node in ast.walk(_parsed(path))
        for name in _imported_names(node)
        if name.startswith("app.engines.pairing")
    ]
    assert len(walked) == 4, [path.name for path in walked]
    assert offenders == [], offenders


def test_the_engine_does_not_import_the_rating_engine_either():
    """``overlap_span`` is a Band width **copied**, and this is what keeps it a copy.

    The rating context owns the 1,0–5,0 scale, the four bands and the confidence
    transform. Match Fit's largest constant is derived from the widest of those bands
    and is written out here rather than read from there, for the reason the pairing
    engine gives for the onboarding σ floor: a Match Fit score that moved because a
    rating lineage retuned could not be attributed to one set of constants, and the
    falsification programme is exactly that attribution.

    What keeps the copy honest is the mirror in the persona suite — the file that is
    *meant* to break on a retune. This walk is the other half: it says the shortcut
    was not taken.
    """

    offenders = [
        f"{path.relative_to(ROOT)}:{node.lineno}: {name}"
        for path in _modules_of(MATCHFIT) + [FIT]
        for node in ast.walk(_parsed(path))
        for name in _imported_names(node)
        if name.startswith("app.engines.racketskill")
    ]
    assert offenders == [], offenders


def _imported_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and not node.level:
        return [node.module or ""]
    return []


def test_every_value_object_in_the_vocabulary_is_frozen_and_closed():
    """``@final`` and ``frozen`` erase into nothing a behaviour test can see.

    The compiler enforces both — ``tests/typecheck/kernel_misuse.py`` proves it, on a
    term subclassed and a score assigned to. What that harness cannot say is whether
    the decorator was applied to each class here, since a dropped one produces no
    error anywhere. So the list is written out: adding a value object means adding a
    line, which is the diff a reviewer should see.
    """

    vocabulary = (
        SkillOverlapFact,
        BalanceFact,
        TimeFact,
        ViabilityFact,
        PriceFact,
        TravelFact,
        MatchTypeFact,
        LadderFact,
        ReliabilityFact,
        FamiliarityFact,
        ScoredTerm,
        ExcludedTerm,
        MatchFitScore,
        Observed,
        MatchFitConstants,
        HourWindow,
        PlayerProfile,
        ClubSnapshot,
        PlayerScore,
        PlayHistory,
    )
    unclosed = [
        cls.__name__ for cls in vocabulary if not getattr(cls, "__final__", False)
    ]
    unfrozen = [
        cls.__name__ for cls in vocabulary if not cls.__dataclass_params__.frozen
    ]
    assert unclosed == [], unclosed
    assert unfrozen == [], unfrozen


def test_a_fourth_ladder_state_would_have_to_be_handled_rather_than_fall_through():
    """The ``case _`` that closes the ladder term's match over the enum.

    ``exhaustive`` makes an unhandled member a *typecheck* failure — which is the
    check that matters, since the enum is closed and no snapshot can carry a fourth
    state. It is asserted at runtime anyway, through a stand-in the brand cannot
    refuse, because the alternative to raising is falling through to a value nobody
    chose: silently full marks for a ladder state the term has never seen.
    """

    class _AFourthState(Enum):
        SOMETHING_ELSE = "something_else"

    weird = replace(doubles(ADA, BO, CY, DEE), ladder=_AFourthState.SOMETHING_ELSE)
    with pytest.raises(AssertionError):
        scored(weird, profile())
