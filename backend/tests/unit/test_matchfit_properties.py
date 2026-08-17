"""Property tests over a seeded sweep: the bounds, and the monotonicities.

A persona pins one card; an invariant pins one identity. These walk a *range* of
inputs and assert the shape of the answer over all of them — the third leg
ADR-0015 prescribes, and the one that catches a curve which is right at both ends
and wrong in the middle.

**Seeded, and the seed is written down.** A property that fails on Tuesday and passes
on Wednesday is not a property; ``random.Random(SEED)`` gives the same sweep on every
machine and every run, and widening the sweep is a diff on a number here.

The sweep is over *declarations, prices, start times and the four facts viability
reads*, never over ratings, because no term in this slice reads a Level. That is the
honest shape of the thing being tested and it is why this file is shorter than the
pairing engine's: two of Match Fit's ten terms are still owed (#86).

**Viability's three monotonicities are asserted at every corner of the other two
inputs**, rather than at a convenient one. A curve that rises with paid seats when the
court is booked and not when it is unheld is not monotone, and one shape of match
would have hidden that.
"""

import random
from dataclasses import replace

import pytest

from app.engines.fit import ExcludedTerm, ScoredTerm, TermCode, TermKind
from app.engines.matchfit.core import measured_share, renormalise, whole_percent
from app.engines.matchfit.v1 import CONSTANTS, MatchFitEngineV1
from app.engines.matchmaking import (
    HOLD_LADDER,
    CourtHold,
    LadderQualification,
    MatchSnapshot,
    MatchTypePreference,
    PlayerProfile,
    PlayerRef,
    PlayHistory,
    SeatState,
    Weekday,
)
from app.kernel import grosze, minutes, ratio, shifted
from tests.unit.matchmaking_snapshots import (
    NOW,
    START,
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
HOLDS = HOLD_LADDER

#: How long before its own start each drawn match closes to joins, in minutes. Two of
#: them are inside the fill window and two are outside it, so the run-up is crossed on
#: both sides of the point where an unpaid seat's chances stop improving.
LEADS = (0, 120, 720, 2880)

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


def paid_states(count: int) -> tuple[SeatState, ...]:
    """Four seated players, ``count`` of whom have paid and the rest merely holding.

    The paid fraction varied **without** varying who is in the match, which is what
    makes a viability sweep a sweep over viability: emptying seats instead would move
    the roster, the familiarity term's company and the reliability term's records all
    at once, and no property could then say which one it had measured.
    """

    return tuple(
        SeatState.PAID if seat < count else SeatState.HELD for seat in range(4)
    )


def drawn(seed: int = SEED):
    """A sweep of (match, declaration) pairs: prices, distances, kinds, ladders — and
    the four facts viability reads.

    Prices run from free to five times the seat share and distances from next door
    to two hours, so every curve is crossed inside its limit, just past it, halfway
    down its span and floored — rather than at whichever point a hand-written case
    happened to pick. The cutoff is drawn as a lead **before the match's own start**,
    which is the only way it can be drawn: a cutoff is a fact about one match, and a
    fixed instant is refused by every match a sweep starts earlier than it.
    """

    rng = random.Random(seed)
    for _ in range(DRAWS):
        payable = rng.randrange(0, 11_000, 50)
        start = starting(day=rng.randrange(0, 7), hour=rng.randrange(0, 24))
        snapshot = replace(
            doubles(
                ADA,
                BO,
                CY,
                DEE,
                travel_minutes=rng.randrange(0, 120),
                counted=rng.choice((True, False)),
                ladder=rng.choice(LADDERS),
                start=start,
                states=paid_states(rng.randrange(0, 5)),
                hold=rng.choice(HOLDS),
                crowding=rng.randrange(0, 101, 10),
                cutoff=shifted(start, minutes(-rng.choice(LEADS))),
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
    assert values[TermCode.MATCH_VIABILITY] == {"full", "part", "zero"}
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


# --- Viability: three monotonicities that survive any retune ----------------------


def viability(snapshot: MatchSnapshot) -> ScoredTerm:
    term = next(
        item
        for item in scored(snapshot, profile()).terms
        if item.code is TermCode.MATCH_VIABILITY
    )
    assert isinstance(term, ScoredTerm)
    return term


#: Every shape the two halves of viability can be in, crossed. Each monotonicity below
#: is asserted **at every one of them**, not at a convenient one: a curve that is
#: monotone with a booked court and not with an unheld one is not monotone.
CORNERS = [
    (hold, crowded, lead)
    for hold in HOLD_LADDER
    for crowded in (0, 50, 100)
    for lead in LEADS
]


@pytest.mark.parametrize("hold, crowded, lead", CORNERS)
def test_a_seat_more_paid_for_never_lowers_viability(hold, crowded, lead):
    """**Monotone non-decreasing in paid seats**, and true under any retune.

    Money down is the strongest thing anybody has said about whether this match will
    be played, so a seat moving from held to paid can never make the platform less
    sure of it. It survives a retune because the only constant on this side is a
    *ceiling* below one — the best an unpaid seat can be worth — and the guard on
    the constants refuses one at or above full marks. At exactly one an unpaid seat
    would be worth as much as a paid one and this curve would go flat, which is the
    flattery the term exists to remove.
    """

    values = [
        viability(
            doubles(
                ADA,
                BO,
                CY,
                DEE,
                states=paid_states(paid),
                hold=hold,
                crowding=crowded,
                cutoff=shifted(START, minutes(-lead)),
            )
        ).value
        for paid in range(5)
    ]
    assert values == sorted(values)


@pytest.mark.parametrize("paid, crowded, lead", [(0, 0, 0), (2, 50, 720), (4, 100, 0)])
def test_a_firmer_hold_never_lowers_viability(paid, crowded, lead):
    """**Monotone non-decreasing in the hold tier**, and true under any retune.

    Walked along ``HOLD_LADDER`` — the *vocabulary's* order, never the constants'
    — which is what makes this survive a retune rather than move with one: the
    constants' guard refuses a mapping that falls along that ladder, so a retune can
    move the rungs apart and cannot swap them.
    """

    values = [
        viability(
            doubles(
                ADA,
                BO,
                CY,
                DEE,
                states=paid_states(paid),
                hold=hold,
                crowding=crowded,
                cutoff=shifted(START, minutes(-lead)),
            )
        ).value
        for hold in HOLD_LADDER
    ]
    assert values == sorted(values)


@pytest.mark.parametrize(
    "hold, paid, lead", [(hold, paid, 0) for hold in HOLD_LADDER for paid in (0, 4)]
)
def test_a_more_crowded_club_never_raises_viability(hold, paid, lead):
    """**Non-increasing in the club's saturation**, and true under any retune.

    A club with less left to give is a match less likely to find a court, and no
    constant here can invert that: crowding enters as the share of the *unheld* part
    of the court side, and that part is never negative.

    At a hard hold the curve is **flat**, which is the case worth reading rather than
    the interesting one: a court you have booked cannot be taken by the club being
    busy, so saturation stops mattering exactly when the court stops being at risk.
    """

    values = [
        viability(
            doubles(
                ADA,
                BO,
                CY,
                DEE,
                states=paid_states(paid),
                hold=hold,
                crowding=crowded,
                cutoff=shifted(START, minutes(-lead)),
            )
        ).value
        for crowded in range(0, 101, 5)
    ]
    assert values == sorted(values, reverse=True)


def test_less_time_to_the_cutoff_never_raises_viability():
    """The run-up, which is the only place ``now`` enters a Match Fit score.

    A seat nobody has taken is worth less the closer the cutoff gets, because there
    is less time for anybody to take it — and at the cutoff it is worth nothing. A
    *full* match does not move at all, which is the second half of the same claim:
    there is nothing left to fill, so there is nothing for the clock to take away.
    """

    for paid, moves in ((0, True), (2, True), (4, False)):
        values = [
            viability(
                doubles(
                    ADA,
                    BO,
                    CY,
                    DEE,
                    states=paid_states(paid),
                    hold=CourtHold.SOFT,
                    cutoff=shifted(NOW, minutes(left)),
                )
            ).value
            # Written as *minutes remaining* and not as a lead before the start,
            # because that is the quantity the term reads and the direction the
            # claim is made in — a lead grows as the time left shrinks, and a
            # property asserted in the wrong direction is one that passes by
            # measuring the opposite of its own docstring.
            for left in range(0, 1_351, 60)
        ]
        assert values == sorted(values)
        assert (values[0] < values[-1]) is moves


def test_viability_is_never_excluded_and_never_lowers_coverage():
    """**The evidence term that is always computable**, over the whole sweep.

    Every other piece of evidence can be missing — and when they all are, an empty
    court scores perfectly on the constraints it trivially satisfies. This one cannot
    be missing, because every match has a phase, a hold, a seat count and a cutoff. It
    is what makes *absence never flatters* true of a ranking rather than only of the
    mechanism.
    """

    for snapshot, declaration in drawn():
        result = scored(snapshot, declaration)
        term = next(
            item for item in result.terms if item.code is TermCode.MATCH_VIABILITY
        )
        assert isinstance(term, ScoredTerm)
        assert term.kind is TermKind.EVIDENCE
        assert term.code not in {excluded.code for excluded in result.excluded}
        assert result.coverage >= whole_percent(
            ratio(
                CONSTANTS.weights[TermCode.MATCH_VIABILITY],
                sum(CONSTANTS.weights.values()),
            )
        )


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
