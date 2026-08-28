"""The group objective: the six terms, the arrangement, and what decided it.

**A four contains six pairs and the searcher is in three of them.** Every
assertion here is ultimately about that sentence: the three cross pairs, the
four-way intersection and the seat delta are the facts no Fit could see, and a
term that read anything else would be charging the searcher's own pairing twice.

**The numbers are re-derived from the live ruleset and never written out.** A
test carrying its own copy of ``16.1 / 31.0`` agrees with the engine right up
until the day somebody releases a different vector — and the one claim these
weights make, that a cross reading is *automatically* worth more in a friendly,
is a claim about the ratio between two released numbers rather than about either
of them.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from app.engines.matchfit.core import (
    ForecastAssumption,
    GroupReason,
    GroupTerm,
    SearchMode,
    Seat,
    Term,
)
from app.engines.matchfit.grouping import (
    Arrangement,
    Forecast,
    GroupScore,
    PersonalFacts,
    Seated,
)
from app.engines.matchfit.ruleset import WEIGHT_TOTAL
from app.engines.matchfit.scorable import LevelReading, Searcher
from app.engines.matchfit.v1.fit import score
from app.engines.matchfit.v1.group import (
    CROSS_TERMS,
    arrange,
    arrangements,
    best,
    cross_reading,
    deciding_reason,
    evenest,
    forecast,
    group_availability,
    objective,
    seat_delta,
)
from app.kernel import InvariantViolated
from app.modules.matchmaking.domain.fence import combine_group_sigma
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.availability import DayPart
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.social_tags import SocialTag
from tests.unit.matchfit_builders import cells, searcher, seated

#: The four-way spread, folded on RacketSkill's side of the fence exactly as the
#: module does it. Written through the composition seam and never as ``√(Σσ²)``,
#: for the reason ``sigma_pair`` is: a test with its own copy of an identity
#: agrees with the engine until the day the rule changes.
COMBINE = combine_group_sigma


#: Three seats, all reading the same defaults, so a test states only what it
#: varies. Ids ascend, because a tie between two arrangements breaks on the
#: partner's id and a test that could not tell which won would be asserting
#: nothing.
def _three() -> tuple[Seated, Seated, Seated]:
    return (
        seated(player_id="a"),
        seated(player_id="b"),
        seated(player_id="c"),
    )


def _four(
    *,
    mode: SearchMode = SearchMode.COMPETITIVE,
    mus: tuple[float, float, float] = (2.80, 2.80, 2.80),
    fits: tuple[float, float, float] = (70.0, 70.0, 70.0),
    tags: tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]] = ((), (), ()),
    intents: tuple[str | None, str | None, str | None] = (None, None, None),
    searcher_tags: tuple[str, ...] = (),
) -> tuple[Searcher, tuple[Seated, Seated, Seated]]:
    """A searcher and three seats, each fact supplied per seat."""

    return searcher(mode=mode, tags=searcher_tags), (
        seated(
            player_id="a",
            mu=mus[0],
            fit=fits[0],
            tags=tags[0],
            declared_intent=intents[0],
        ),
        seated(
            player_id="b",
            mu=mus[1],
            fit=fits[1],
            tags=tags[1],
            declared_intent=intents[1],
        ),
        seated(
            player_id="c",
            mu=mus[2],
            fit=fits[2],
            tags=tags[2],
            declared_intent=intents[2],
        ),
    )


# ---------------------------------------------------------------------------
# The six terms, and the two vectors
# ---------------------------------------------------------------------------


def test_the_objective_is_exactly_six_terms_and_G_is_their_sum() -> None:
    """``G`` is the contributions and nothing else — there is no seventh line."""

    viewer, three = _four(
        tags=((SocialTag.PLAYS_TO_WIN.value,),) * 3,
        intents=(PlayIntent.COMPETITIVE.value,) * 3,
        searcher_tags=(SocialTag.PLAYS_TO_WIN.value,),
    )
    scored = objective(viewer, Arrangement.all_of(three)[0], LIVE_RULESET, COMBINE)

    assert {reading.term for reading in scored.terms} == set(GroupTerm)
    assert len(GroupTerm) == 6
    assert scored.objective == pytest.approx(
        sum(reading.contribution for reading in scored.terms)
    )
    assert scored.degraded_terms == ()


def test_G_is_a_property_of_its_terms_and_never_a_field() -> None:
    """There is no constructor that takes an already-summed objective.

    A field could hold a number its own terms do not add up to, and a field is
    also what a serialiser reaches for. ``G`` is never returned as a number, and
    the strongest form of that is having nothing to return.
    """

    assert "objective" not in {field.name for field in dataclasses.fields(GroupScore)}


def test_the_inversion_arrives_without_being_asserted() -> None:
    """Competitive puts its weight on the searcher's seats; for fun on the four.

    Two independent inversions, and neither is a constant anybody typed twice:
    the group vector moves the weight, and the *cross reading itself* is richer
    in a friendly because more than half of a for-fun Fit is person-to-person
    against under a third of a competitive one.
    """

    group = LIVE_RULESET.group.weights
    own = (GroupTerm.SEAT_FIT, GroupTerm.MIN_SEAT_FIT)
    cross = (GroupTerm.CROSS, GroupTerm.CROSS_MIN)

    comp, fun = group[SearchMode.COMPETITIVE], group[SearchMode.FOR_FUN]
    assert sum(comp[term] for term in cross) < sum(comp[term] for term in own)
    assert sum(fun[term] for term in cross) > sum(fun[term] for term in own)

    def person_to_person(mode: SearchMode) -> float:
        weights = LIVE_RULESET.modes[mode].weights
        live = sum(weights[term] for term in Term if term is not Term.RELIABILITY)
        return sum(weights[term] for term in CROSS_TERMS) / live

    assert person_to_person(SearchMode.FOR_FUN) > person_to_person(
        SearchMode.COMPETITIVE
    )


# ---------------------------------------------------------------------------
# The cross reading
# ---------------------------------------------------------------------------


def test_a_cross_reading_is_fits_own_sub_score_renormalised() -> None:
    """It invents no constant: the shares are Fit's own three weights, rescaled.

    Re-derived here from the ruleset rather than compared against a literal, so
    that a weight release moves the expectation with the engine — the assertion
    is the *identity*, not today's numbers.
    """

    mine = PersonalFacts(
        declared_intent=PlayIntent.COMPETITIVE.value,
        tags=(SocialTag.PLAYS_TO_WIN.value, SocialTag.STAYS_FOR_A_DRINK.value),
    )
    theirs = PersonalFacts(
        declared_intent=PlayIntent.COMPETITIVE.value,
        tags=(SocialTag.PLAYS_TO_WIN.value, SocialTag.STAYS_FOR_A_DRINK.value),
    )
    reading = cross_reading(
        SearchMode.COMPETITIVE, mine, theirs, Seat.OPPONENT, LIVE_RULESET
    )

    weights = LIVE_RULESET.modes[SearchMode.COMPETITIVE].weights
    basis = sum(weights[term] for term in CROSS_TERMS)
    intent = LIVE_RULESET.intent.alignment[SearchMode.COMPETITIVE][
        PlayIntent.COMPETITIVE.value
    ]
    style = 1.0 - LIVE_RULESET.tags.phi
    vibe = 1.0 - LIVE_RULESET.tags.phi
    cap = LIVE_RULESET.tags.clash_cap
    expected = (
        weights[Term.INTENT_ALIGNMENT] * intent
        + weights[Term.PLAYING_STYLE] * (style + cap) / (1.0 + cap)
        + weights[Term.SOCIAL_VIBE] * (vibe + cap) / (1.0 + cap)
    ) / basis

    assert reading == pytest.approx(expected)


def test_the_intent_component_of_a_cross_reading_is_the_documented_share() -> None:
    """0.519 competitive and 0.298 for fun — and both fall out of the vector.

    The two figures are ``docs/adr/0117``'s, and they are what makes
    ``w_crossmin`` earn its place on intent rather than on clashes. Asserted as
    the ratio the ADR computed rather than as a number, so the claim survives a
    release and a wrong release fails here.
    """

    for mode in SearchMode:
        weights = LIVE_RULESET.modes[mode].weights
        share = weights[Term.INTENT_ALIGNMENT] / sum(
            weights[term] for term in CROSS_TERMS
        )
        agreed = PersonalFacts(
            declared_intent=LIVE_RULESET.intent.same_evening[mode], tags=()
        )
        other_mode = next(one for one in SearchMode if one is not mode)
        opposed = PersonalFacts(
            declared_intent=LIVE_RULESET.intent.same_evening[other_mode], tags=()
        )

        together = cross_reading(mode, agreed, agreed, Seat.OPPONENT, LIVE_RULESET)
        apart = cross_reading(mode, agreed, opposed, Seat.OPPONENT, LIVE_RULESET)
        assert together == pytest.approx(1.0)
        assert apart == pytest.approx(0.0)
        assert share == pytest.approx(
            {SearchMode.COMPETITIVE: 0.519, SearchMode.FOR_FUN: 0.298}[mode],
            abs=0.001,
        )

        # And with all three components live, so the drop is the share rather
        # than the whole reading: the ADR's own 0.519 / 0.298, worth 4.5 and 6.2
        # points through the min and its share of the mean.
        tags = (SocialTag.PLAYS_TO_WIN.value, SocialTag.STAYS_FOR_A_DRINK.value)
        matched = PersonalFacts(declared_intent=agreed.declared_intent, tags=tags)
        crossed = PersonalFacts(declared_intent=opposed.declared_intent, tags=tags)
        drop = cross_reading(
            mode, matched, matched, Seat.OPPONENT, LIVE_RULESET
        ) - cross_reading(mode, matched, crossed, Seat.OPPONENT, LIVE_RULESET)
        assert drop == pytest.approx(share)

        group = LIVE_RULESET.group.weights[mode]
        points = group[GroupTerm.CROSS_MIN] * drop + group[GroupTerm.CROSS] * drop / 3
        assert points == pytest.approx(
            {SearchMode.COMPETITIVE: 4.5, SearchMode.FOR_FUN: 6.2}[mode], abs=0.05
        )


def test_an_opposed_cross_pair_zeroes_the_intent_component_in_both_modes() -> None:
    """The table's zero sits in competitive only; the pair reads it in both.

    A cross pair contains no searcher, so each declaration selects the vector it
    would itself be judged under and the pair takes **the worse of the two
    readings** — an evening is only as shared as its less-satisfied half. One
    direction of an opposed pair always reads the zero, whichever mode the search
    is in.
    """

    competitive = PersonalFacts(declared_intent=PlayIntent.COMPETITIVE.value, tags=())
    for_fun = PersonalFacts(declared_intent=PlayIntent.FOR_FUN.value, tags=())

    for mode in SearchMode:
        assert cross_reading(
            mode, competitive, for_fun, Seat.OPPONENT, LIVE_RULESET
        ) == pytest.approx(0.0)


def test_a_cross_reading_is_symmetric() -> None:
    """A pair with no searcher in it has no *mine* for an asymmetry to point at."""

    one = PersonalFacts(
        declared_intent=PlayIntent.COMPETITIVE.value,
        tags=(SocialTag.HERE_TO_IMPROVE.value,),
    )
    other = PersonalFacts(
        declared_intent=PlayIntent.NO_PREFERENCE.value,
        tags=(SocialTag.WARMS_UP_PROPERLY.value,),
    )
    forward = cross_reading(
        SearchMode.COMPETITIVE, one, other, Seat.OPPONENT, LIVE_RULESET
    )
    backward = cross_reading(
        SearchMode.COMPETITIVE, other, one, Seat.OPPONENT, LIVE_RULESET
    )
    assert forward == backward


def test_a_cross_pair_nobody_can_read_stands_down_rather_than_reading_zero() -> None:
    """Two people who declared nothing and hold no tag are not a zero."""

    silent = PersonalFacts(declared_intent=None, tags=())
    assert (
        cross_reading(
            SearchMode.COMPETITIVE, silent, silent, Seat.OPPONENT, LIVE_RULESET
        )
        is None
    )


# ---------------------------------------------------------------------------
# The seat delta
# ---------------------------------------------------------------------------


def test_the_seat_delta_is_what_the_partner_reading_costs() -> None:
    """``TALKS_THROUGH_THE_MATCH`` beside ``QUIET_AND_FOCUSED`` is worse seated.

    Two rows with disjoint seat scopes — real as partners, mild across the net —
    so the delta is signed, negative, and needed no new constant to say it.
    """

    viewer = searcher(
        mode=SearchMode.COMPETITIVE, tags=(SocialTag.TALKS_THROUGH_THE_MATCH.value,)
    )
    partner = seated(player_id="a", tags=(SocialTag.QUIET_AND_FOCUSED.value,))

    delta = seat_delta(viewer, partner, LIVE_RULESET)
    mine = PersonalFacts.of_searcher(viewer, LIVE_RULESET.intent)
    assert delta == pytest.approx(
        cross_reading(viewer.mode, mine, partner.personal, Seat.PARTNER, LIVE_RULESET)
        - cross_reading(
            viewer.mode, mine, partner.personal, Seat.OPPONENT, LIVE_RULESET
        )
    )
    assert delta < 0.0


def test_the_seat_delta_is_zero_where_no_partner_scoped_row_fires() -> None:
    """Unseated already reads ``OPPONENT``, so an opponent seat gains nothing.

    That is the whole of *exactly zero for opponent seats by construction*: the
    delta is the difference between two readings, and outside the handful of
    seat-scoped rows the two readings are the same reading.
    """

    viewer = searcher(tags=(SocialTag.PLAYS_TO_WIN.value,))
    partner = seated(player_id="a", tags=(SocialTag.PLAYS_TO_WIN.value,))
    assert seat_delta(viewer, partner, LIVE_RULESET) == pytest.approx(0.0)


def test_the_seat_delta_never_re_scores_a_fit() -> None:
    """The card said 78 in the shortlist and it says 78 in the builder.

    The delta is real here — the pair carries the seat-scoped clash — and the
    printed Fit is unmoved by it, because the objective reads the number it was
    handed and has no way to write one back.
    """

    viewer = searcher(tags=(SocialTag.TALKS_THROUGH_THE_MATCH.value,))
    seat = seated(player_id="a", tags=(SocialTag.QUIET_AND_FOCUSED.value,), fit=78.0)
    others = (seated(player_id="b"), seated(player_id="c"))

    assert seat_delta(viewer, seat, LIVE_RULESET) < 0.0
    unseated = score(viewer, seat.candidate, LIVE_RULESET)
    chosen = arrange(viewer, (seat, *others), LIVE_RULESET, COMBINE)
    for member in chosen.arrangement.seated:
        if member.player_id == "a":
            assert member.fit == 78.0
    assert score(viewer, seat.candidate, LIVE_RULESET).points == unseated.points


# ---------------------------------------------------------------------------
# Group availability
# ---------------------------------------------------------------------------


def test_group_availability_is_the_intersection_over_the_smallest_grid() -> None:
    """Among four people there is no *mine*, so the denominator is the least."""

    monday = cells((1, DayPart.EVENING))
    two = cells((1, DayPart.EVENING), (3, DayPart.EVENING))
    three = cells((1, DayPart.EVENING), (3, DayPart.EVENING), (5, DayPart.EVENING))

    assert group_availability((three, three, two, monday)) == pytest.approx(1.0)
    assert group_availability((three, three, three, two)) == pytest.approx(1.0)
    assert group_availability((three, two, two, cells((3, DayPart.EVENING)))) == (
        pytest.approx(1.0)
    )


def test_three_good_pairwise_overlaps_do_not_imply_a_four_way_one() -> None:
    """The failure no Fit can see, and the whole argument for the term."""

    monday = cells((1, DayPart.EVENING))
    tuesday = cells((2, DayPart.EVENING))
    both = cells((1, DayPart.EVENING), (2, DayPart.EVENING))

    assert group_availability((both, monday, tuesday, monday)) == 0.0


def test_group_availability_is_a_term_and_never_a_gate() -> None:
    """An empty intersection docks the four; it never removes it."""

    viewer = searcher(grid=cells((1, DayPart.EVENING)))
    three = (
        seated(player_id="a", grid=cells((2, DayPart.EVENING))),
        seated(player_id="b", grid=cells((1, DayPart.EVENING))),
        seated(player_id="c", grid=cells((1, DayPart.EVENING))),
    )
    scored = objective(viewer, Arrangement.all_of(three)[0], LIVE_RULESET, COMBINE)

    availability = next(
        reading for reading in scored.terms if reading.term is GroupTerm.AVAILABILITY
    )
    assert availability.value == 0.0
    assert availability.contribution == 0.0
    assert scored.objective > 0.0


def test_a_blank_grid_stands_the_term_down_rather_than_reading_zero() -> None:
    """*Blank means we do not know* is not *you four never overlap*."""

    assert group_availability((cells((1, DayPart.EVENING)), (), (), ())) is None

    viewer = searcher()
    three = (
        seated(player_id="a", grid=()),
        seated(player_id="b"),
        seated(player_id="c"),
    )
    scored = objective(viewer, Arrangement.all_of(three)[0], LIVE_RULESET, COMBINE)
    assert GroupTerm.AVAILABILITY in scored.degraded_terms
    assert all(reading.term is not GroupTerm.AVAILABILITY for reading in scored.terms)


def test_a_term_that_stands_down_renormalises_the_survivors() -> None:
    """The same rule Fit runs on: the shares of what fired sum to a hundred."""

    viewer = searcher()
    three = (
        seated(player_id="a", grid=()),
        seated(player_id="b"),
        seated(player_id="c"),
    )
    scored = objective(viewer, Arrangement.all_of(three)[0], LIVE_RULESET, COMBINE)
    assert sum(reading.weight for reading in scored.terms) == pytest.approx(
        WEIGHT_TOTAL
    )


# ---------------------------------------------------------------------------
# The seats' own Fits
# ---------------------------------------------------------------------------


def test_the_mean_and_the_min_read_the_unlocked_seats_only() -> None:
    """A locked poor Fit would pin the min across every combination.

    A constant in an argmax is not a term, and ``w_minfit`` going inert in the
    one mode where seats are locked is exactly ADR-0103's *blind over the range
    it is asked to score*, one stage further on.
    """

    viewer = searcher()
    three = (
        seated(player_id="a", fit=20.0, locked=True),
        seated(player_id="b", fit=80.0),
        seated(player_id="c", fit=60.0),
    )
    scored = objective(viewer, Arrangement.all_of(three)[0], LIVE_RULESET, COMBINE)

    minimum = next(
        reading for reading in scored.terms if reading.term is GroupTerm.MIN_SEAT_FIT
    )
    mean = next(
        reading for reading in scored.terms if reading.term is GroupTerm.SEAT_FIT
    )
    assert minimum.value == pytest.approx(0.60)
    assert mean.value == pytest.approx(0.70)


def test_a_four_of_locked_seats_stands_both_own_seat_terms_down() -> None:
    """Nothing is left to compare, so the two terms report nothing rather than 0."""

    viewer = searcher()
    three = (
        seated(player_id="a", fit=20.0, locked=True),
        seated(player_id="b", fit=80.0, locked=True),
        seated(player_id="c", fit=60.0, locked=True),
    )
    scored = objective(viewer, Arrangement.all_of(three)[0], LIVE_RULESET, COMBINE)
    assert GroupTerm.SEAT_FIT in scored.degraded_terms
    assert GroupTerm.MIN_SEAT_FIT in scored.degraded_terms


def test_the_worst_seat_is_priced_against_the_mean() -> None:
    """Fits of 90 / 88 / 46 lose to 72 / 71 / 70 — the ADR's worked contrast."""

    viewer = searcher()
    lopsided = arrange(
        viewer,
        (
            seated(player_id="a", fit=90.0),
            seated(player_id="b", fit=88.0),
            seated(player_id="c", fit=46.0),
        ),
        LIVE_RULESET,
        COMBINE,
    )
    even = arrange(
        viewer,
        (
            seated(player_id="a", fit=72.0),
            seated(player_id="b", fit=71.0),
            seated(player_id="c", fit=70.0),
        ),
        LIVE_RULESET,
        COMBINE,
    )
    assert even.objective > lopsided.objective


# ---------------------------------------------------------------------------
# The arrangement
# ---------------------------------------------------------------------------


def test_there_are_exactly_three_arrangements_and_each_seats_a_different_partner() -> (
    None
):
    """An arrangement of a four is fully described by who partners the searcher."""

    three = _three()
    all_three = Arrangement.all_of(three)
    assert len(all_three) == 3
    assert {one.partner.player_id for one in all_three} == {"a", "b", "c"}
    for one in all_three:
        assert len(one.cross_pairs) == 3
        assert sum(1 for pair in one.cross_pairs if pair.seat is Seat.PARTNER) == 1
        # The three pairs among the three seated, and no others: a cross pair is
        # typed as two `Seated`, so the searcher cannot appear in one at all.
        assert {
            frozenset((pair.mine.player_id, pair.theirs.player_id))
            for pair in one.cross_pairs
        } == {frozenset(("a", "b")), frozenset(("a", "c")), frozenset(("b", "c"))}


@pytest.mark.parametrize("mode", list(SearchMode))
@pytest.mark.parametrize(
    "mus", [(2.60, 2.80, 3.10), (3.00, 3.00, 3.00), (2.50, 3.40, 2.95)]
)
@pytest.mark.parametrize("fits", [(70.0, 70.0, 70.0), (81.0, 64.0, 55.0)])
def test_arrange_returns_argmax_G_brute_forced_over_all_three(
    mode: SearchMode,
    mus: tuple[float, float, float],
    fits: tuple[float, float, float],
) -> None:
    """``arrange()`` is not a separate step — it is the argmax, and nothing else.

    Brute-forced over the three rather than trusted, because the shape this
    replaces *did* pick the min-gap arrangement and hand it to the objective, and
    the two agree on almost every four.
    """

    viewer, three = _four(
        mode=mode,
        mus=mus,
        fits=fits,
        tags=(
            (SocialTag.PLAYS_TO_WIN.value,),
            (SocialTag.QUIET_AND_FOCUSED.value,),
            (SocialTag.TALKS_THROUGH_THE_MATCH.value,),
        ),
        intents=(
            PlayIntent.COMPETITIVE.value,
            PlayIntent.FOR_FUN.value,
            PlayIntent.NO_PREFERENCE.value,
        ),
        searcher_tags=(SocialTag.PLAYS_TO_WIN.value,),
    )
    every = arrangements(viewer, three, LIVE_RULESET, COMBINE)
    chosen = arrange(viewer, three, LIVE_RULESET, COMBINE)

    assert chosen.objective == pytest.approx(max(one.objective for one in every))
    assert chosen == best(every)


def test_x3_an_opposed_intent_cross_pair_loses_to_an_otherwise_equal_four() -> None:
    """§4's contrast X3, as an ordered outcome rather than an assertion.

    *One person keeping score in a four where three want a beer*, priced for the
    two people Fit never asked about — the searcher's own three Fits are
    identical in both fours, so nothing but the cross pairs can have decided it.
    This is what ``w_crossmin`` earns its place on.
    """

    for mode in SearchMode:
        wants = LIVE_RULESET.intent.same_evening[mode]
        other = LIVE_RULESET.intent.same_evening[
            next(one for one in SearchMode if one is not mode)
        ]
        viewer = searcher(mode=mode)

        def four(*declarations: str) -> tuple[Seated, Seated, Seated]:
            first, second, third = declarations
            return (
                seated(player_id="a", declared_intent=first),
                seated(player_id="b", declared_intent=second),
                seated(player_id="c", declared_intent=third),
            )

        agreed = arrange(viewer, four(wants, wants, wants), LIVE_RULESET, COMBINE)
        opposed = arrange(viewer, four(wants, wants, other), LIVE_RULESET, COMBINE)
        assert opposed.objective < agreed.objective


def test_x6_the_arrangement_that_does_not_seat_a_clash_together_wins() -> None:
    """§4's contrast X6: two arrangements at identical balance, one clash apart.

    A near-tie claim, and the spec records that its first draft was wrong — the
    tag arms break ties at group level, they do not win against a real
    advantage. So the four is levelled first, which is the only condition under
    which the claim was ever true.
    """

    viewer = searcher(mu=3.10, tags=(SocialTag.TALKS_THROUGH_THE_MATCH.value,))
    three = (
        seated(player_id="a", mu=3.10, tags=(SocialTag.QUIET_AND_FOCUSED.value,)),
        seated(player_id="b", mu=3.10, tags=(SocialTag.PLAYS_TO_WIN.value,)),
        seated(player_id="c", mu=3.10, tags=(SocialTag.PLAYS_TO_WIN.value,)),
    )
    every = arrangements(viewer, three, LIVE_RULESET, COMBINE)
    assert all(one.side_gap == pytest.approx(0.0) for one in every)

    beside_the_clash = next(
        one for one in every if one.arrangement.partner.player_id == "a"
    )
    apart = [one for one in every if one.arrangement.partner.player_id != "a"]
    assert all(one.objective > beside_the_clash.objective for one in apart)


def test_the_three_arrangements_span_the_documented_gaps() -> None:
    """A four at 3.0 / 3.2 / 3.5 / 3.8 spans 0.025, 0.245 and 0.545.

    ``the-group-objective.md`` §3.1's own worked figures, which are what its
    *fifty to one* comparison against the seat delta rests on. They exist only
    because a side's strength is not the average of two players: at parity every
    arrangement of the same people would forecast the same game.
    """

    viewer = searcher(mu=3.00)
    three = (
        seated(player_id="a", mu=3.20),
        seated(player_id="b", mu=3.50),
        seated(player_id="c", mu=3.80),
    )
    gaps = sorted(
        round(one.side_gap, 3)
        for one in arrangements(viewer, three, LIVE_RULESET, COMBINE)
    )
    assert gaps == [0.025, 0.245, 0.545]


def test_best_and_evenest_differ_exactly_where_balance_has_nothing_to_say() -> None:
    """The new fact the builder can state, and the seat delta's own falsifier.

    With a level spread, balance dominates and the two agree. With four
    near-equal levels the gaps collapse and the seat delta decides — which is
    ADR-0117's shape arriving on its own rather than being asserted.
    """

    viewer = searcher(mu=3.10, tags=(SocialTag.TALKS_THROUGH_THE_MATCH.value,))

    def four(mus: tuple[float, float, float]) -> tuple[Seated, Seated, Seated]:
        """``a`` is the one the searcher should not be seated beside."""

        return (
            seated(player_id="a", mu=mus[0], tags=(SocialTag.QUIET_AND_FOCUSED.value,)),
            seated(player_id="b", mu=mus[1], tags=(SocialTag.PLAYS_TO_WIN.value,)),
            seated(player_id="c", mu=mus[2], tags=(SocialTag.PLAYS_TO_WIN.value,)),
        )

    assert seat_delta(viewer, four((3.10, 3.10, 3.10))[0], LIVE_RULESET) < 0.0

    apart = arrangements(viewer, four((3.00, 3.05, 3.20)), LIVE_RULESET, COMBINE)
    assert len({round(one.side_gap, 4) for one in apart}) == 3
    assert best(apart) is evenest(apart)

    flat = arrangements(viewer, four((3.10, 3.10, 3.10)), LIVE_RULESET, COMBINE)
    assert all(one.side_gap == pytest.approx(0.0) for one in flat)
    assert evenest(flat).arrangement.partner.player_id == "a"
    assert best(flat).arrangement.partner.player_id == "b"


# ---------------------------------------------------------------------------
# The forecast
# ---------------------------------------------------------------------------


def test_provisional_travels_inside_the_forecast() -> None:
    """The number and its caveat are one value, so a refactor cannot part them."""

    assert "provisional" not in {field.name for field in dataclasses.fields(Forecast)}
    settled = Forecast(pct=71, sigma_group=0.5, assumption=None)
    guessed = Forecast(
        pct=71,
        sigma_group=0.5,
        assumption=ForecastAssumption.EMPTY_SEAT_MATCHES_ITS_PARTNER,
    )
    assert not settled.provisional
    assert guessed.provisional


@pytest.mark.parametrize(
    "levels",
    [
        (2.80, 3.10, 2.95),
        (3.40, 2.60, 3.00),
        (2.50, 2.50, 2.50),
    ],
)
def test_provisional_equals_arranged_the_moment_the_last_seat_fills(
    levels: tuple[float, float, float],
) -> None:
    """One implementation produces both figures, so the equality is a property.

    A half-empty side is read as if the missing player matched the one already
    there — implemented by seating that player twice — so filling the seat with
    the player the assumption named leaves the figure untouched and lifts only
    the caveat. That is the caveat being honest, asserted rather than hoped.
    """

    alone = LevelReading(mu=levels[0], sigma=0.30)
    other = (
        LevelReading(mu=levels[1], sigma=0.28),
        LevelReading(mu=levels[2], sigma=0.41),
    )

    partial = forecast((alone,), other, LIVE_RULESET.balance, COMBINE)
    filled = forecast((alone, alone), other, LIVE_RULESET.balance, COMBINE)

    assert partial.pct == filled.pct
    assert partial.sigma_group == pytest.approx(filled.sigma_group)
    assert partial.provisional
    assert partial.assumption is ForecastAssumption.EMPTY_SEAT_MATCHES_ITS_PARTNER
    assert not filled.provisional


def test_a_side_with_nobody_on_it_is_not_a_side() -> None:
    """Refused rather than forecast, because there is nothing to assume about."""

    with pytest.raises(InvariantViolated, match="an empty side is not a side"):
        forecast((), (LevelReading(mu=3.0, sigma=0.3),), LIVE_RULESET.balance, COMBINE)


def test_the_group_sigma_is_combined_outside_the_engine() -> None:
    """Quadrature has one owner, and a fold of it is not a second rule."""

    sigmas = [0.30, 0.28, 0.41, 0.35]
    assert combine_group_sigma(sigmas) == pytest.approx(
        math.sqrt(sum(sigma * sigma for sigma in sigmas))
    )


# ---------------------------------------------------------------------------
# The reason code
# ---------------------------------------------------------------------------


def test_every_group_term_names_a_code_and_the_two_cross_terms_share_one() -> None:
    """Six terms and five codes: *these four get on* is one sentence, not two."""

    assert {term.reason for term in GroupTerm} == set(GroupReason)
    assert GroupTerm.CROSS.reason is GroupReason.GROUP_RAPPORT
    assert GroupTerm.CROSS_MIN.reason is GroupReason.GROUP_RAPPORT


def test_the_deciding_reason_names_the_largest_winner_to_runner_up_margin() -> None:
    """Over contributions, because a term is only as deciding as its weight."""

    viewer = searcher()
    winner = arrange(
        viewer,
        (
            seated(player_id="a", fit=70.0),
            seated(player_id="b", fit=70.0),
            seated(player_id="c", fit=70.0),
        ),
        LIVE_RULESET,
        COMBINE,
    )
    runner_up = arrange(
        viewer,
        (
            seated(player_id="a", fit=70.0, grid=cells((7, DayPart.MORNING))),
            seated(player_id="b", fit=70.0),
            seated(player_id="c", fit=70.0),
        ),
        LIVE_RULESET,
        COMBINE,
    )
    assert deciding_reason(winner, runner_up) is GroupReason.MOST_SHARED_SLOTS

    thinner = arrange(
        viewer,
        (
            seated(player_id="a", fit=40.0),
            seated(player_id="b", fit=70.0),
            seated(player_id="c", fit=70.0),
        ),
        LIVE_RULESET,
        COMBINE,
    )
    assert deciding_reason(winner, thinner) is GroupReason.STRONGEST_WEAKEST_SEAT


# ---------------------------------------------------------------------------
# What is struck, and stays struck
# ---------------------------------------------------------------------------


def test_the_struck_terms_are_absent_from_the_roster() -> None:
    """Raw-tag coherence, intent coherence and the superadditive bonus are gone.

    A roster test rather than a review, because the six that survive are the six
    that read something no seat's Fit read, and a seventh would be somebody
    charging the searcher's own pairing twice.
    """

    assert {term.value for term in GroupTerm} == {
        "BALANCE",
        "SEAT_FIT",
        "MIN_SEAT_FIT",
        "CROSS",
        "CROSS_MIN",
        "AVAILABILITY",
    }
    assert set(vars(LIVE_RULESET.group)) == {"weights", "k"}


def test_the_seat_multipliers_are_absent_and_the_matrix_carries_the_asymmetry() -> None:
    """The seat scope says it once; a blanket scalar would say it a third time."""

    assert not any("MULTIPLIER" in name.upper() for name in vars(LIVE_RULESET.tags))
    scoped = [
        row
        for row in LIVE_RULESET.tags.relationship_matrix
        if set(row.seats) != set(Seat)
    ]
    assert scoped, "the partner asymmetry is carried by the matrix or by nothing"


def test_there_is_no_group_objective_for_a_line_up_with_an_open_seat() -> None:
    """``G`` over fewer than three guests is not a lower ``G``, it is no ``G``.

    With two seats the mean and the min are the same number, there are no cross
    pairs and there is no seat delta, so the objective reduces to a transform of
    Fit that is **not order-preserving** — the line-up route and the search route
    could then name different best candidates for one search. The arrangement
    itself is legitimate, because *three of four* is an honest answer with a
    forecast on it; what is refused is scoring one.
    """

    only = Arrangement.all_of((seated(player_id="a"),))
    assert len(only) == 1 and not only[0].complete
    with pytest.raises(InvariantViolated):
        objective(searcher(), only[0], LIVE_RULESET, COMBINE)


def test_the_candidate_cap_stands_at_the_engine_side_ceiling() -> None:
    """Cubic enumeration is why ``K`` is not *just a config change* in Python."""

    from app.engines.matchfit.core import K_CEILING

    assert LIVE_RULESET.group.k == K_CEILING == 24
