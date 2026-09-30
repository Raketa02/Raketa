"""The eight terms, one behaviour at a time.

``test_matchfit_judged_pairings.py`` proves the arithmetic reproduces the numbers
somebody judged by hand. This file proves the **rules around** that arithmetic —
which are where the term set is actually fragile, because every one of them is a
place a wrong answer looks like a plausible one:

*a stand-down is not a zero*, *a zero is a measurement*, *a strand below the bar
is absent rather than nought*, *a tag about the person may be shown and never
scored*, *the unseated pair reads the more forgiving row*.

Each of those is a sentence somebody could satisfy by accident and nobody would
notice going wrong, which is exactly the definition of a thing that needs a test.
"""

from __future__ import annotations

import dataclasses

import pytest

from app.engines.matchfit.core import (
    ClashSeverity,
    DegradedReason,
    LevelDirection,
    ReliabilityStrand,
    SearchMode,
    Seat,
    TagColumn,
    TagRelationshipKind,
    Term,
)
from app.engines.matchfit.ruleset import TagRelationship
from app.engines.matchfit.evidence import (
    AvailabilityOverlapEvidence,
    DistanceEvidence,
    IntentAlignmentEvidence,
    LevelFitEvidence,
    PlayingStyleEvidence,
    PredictedBalanceEvidence,
    ReliabilityEvidence,
    SharedSlot,
    SocialVibeEvidence,
)
from app.engines.matchfit.scorable import GridCell
from app.engines.matchfit.scoring import StoodDown
from app.engines.matchfit.v1.terms import (
    TermReading,
    availability_overlap,
    distance,
    intent_alignment,
    level_fit,
    playing_style,
    predicted_balance,
    read_terms,
    reliability,
    social_vibe,
)
from app.kernel import InvariantViolated, iso_weekday
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.social_tags import SocialTag
from app.modules.player_profile.domain.weekly_hours import HOURS_OF_THE_DAY
from tests.unit.matchfit_builders import candidate, cells, record, searcher

COMP = LIVE_RULESET.modes[SearchMode.COMPETITIVE]
FUN = LIVE_RULESET.modes[SearchMode.FOR_FUN]


# ---------------------------------------------------------------------------
# Level fit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("their_mu", "direction"),
    [
        (3.20, LevelDirection.ABOVE),
        (2.80, LevelDirection.LEVEL),
        (2.40, LevelDirection.BELOW),
    ],
)
def test_level_fit_names_which_side_of_the_searcher_they_sit_on(
    their_mu: float, direction: LevelDirection
) -> None:
    """A code and not a sign on ``delta``: the sentence differs in all three cases."""

    reading = level_fit(searcher(), candidate(mu=their_mu), COMP)
    assert reading is not None
    assert isinstance(reading.evidence, LevelFitEvidence)
    assert reading.evidence.direction is direction
    assert reading.evidence.delta == pytest.approx(abs(their_mu - 2.80))


def test_the_free_band_is_the_whole_difference_between_the_two_curves() -> None:
    """*A friendly against someone a quarter-point above you is no worse.*

    A quarter of a point costs nearly half the term in a counted game and almost
    nothing in a friendly — and that is a claim about the game, not about the
    weight. Competitive has no band at all: every tenth of a point is priced from
    zero.
    """

    inside_the_band = candidate(mu=2.80 + 0.20)
    competitive = level_fit(searcher(), inside_the_band, COMP)
    friendly = level_fit(searcher(mode=SearchMode.FOR_FUN), inside_the_band, FUN)
    assert competitive is not None and friendly is not None
    assert friendly.value == 1.0
    assert competitive.value < 0.7


def test_level_fit_reaches_zero_at_the_tolerance_and_never_goes_under() -> None:
    """The tolerance **is** the gate, so the curve's zero is the gate's edge.

    One number per mode and not two, which is what stops the gate and the curve
    drifting apart — and the clamp is what stops a candidate the gate would have
    excluded scoring a negative contribution if one ever reaches here.
    """

    for mode, rules in ((SearchMode.COMPETITIVE, COMP), (SearchMode.FOR_FUN, FUN)):
        at_the_edge = level_fit(
            searcher(mode=mode), candidate(mu=2.80 + rules.level_tolerance), rules
        )
        far_past_it = level_fit(searcher(mode=mode), candidate(mu=5.00), rules)
        assert at_the_edge is not None and far_past_it is not None
        assert at_the_edge.value == pytest.approx(0.0)
        assert far_past_it.value == 0.0


def test_level_fit_never_reads_a_band() -> None:
    """The tolerance is absolute on μ, so the same gap costs the same anywhere.

    The shipped bands are deliberately uneven because *evidence* is unevenly
    available down the scale, not because a tenth of a point means less at the
    top — a band-relative tolerance would read a claim about proof as a claim
    about play. Two pairs a tenth apart, one at the bottom of the scale and one
    at the top, and the readings are identical.
    """

    low = level_fit(searcher(mu=1.20), candidate(mu=1.30), COMP)
    high = level_fit(searcher(mu=4.60), candidate(mu=4.70), COMP)
    assert low is not None and high is not None
    assert low.value == pytest.approx(high.value)


# ---------------------------------------------------------------------------
# Predicted balance
# ---------------------------------------------------------------------------


def test_predicted_balance_normalises_across_its_clamp_and_not_across_a_hundred() -> (
    None
):
    """**The clamp bounds are the term's zero and one, not cosmetics.**

    A pairing at the floor reads exactly zero rather than the 0.35 a
    normalisation over ``[0, 100]`` would give it, which is what makes the bottom
    third of the range mean something.
    """

    hopeless = predicted_balance(searcher(), candidate(mu=5.00), LIVE_RULESET.balance)
    assert hopeless is not None
    assert hopeless.value == 0.0
    assert isinstance(hopeless.evidence, PredictedBalanceEvidence)
    assert hopeless.evidence.pct == LIVE_RULESET.balance.pct_min


def test_predicted_balance_prints_both_sigmas_and_never_the_combination() -> None:
    """The two σs are facts about people; the combined one is arithmetic.

    ``confidence`` is the platform's **existing** transform over the combined σ
    and never a second spelling of certainty — and it is never 100, because the
    platform cannot tell a player it is certain about them.
    """

    reading = predicted_balance(
        searcher(sigma=0.34),
        candidate(sigma=0.62, against_sigma=0.34),
        LIVE_RULESET.balance,
    )
    assert reading is not None
    assert isinstance(reading.evidence, PredictedBalanceEvidence)
    assert (reading.evidence.my_sigma, reading.evidence.their_sigma) == (0.34, 0.62)
    assert 0 <= reading.evidence.confidence <= 99


# ---------------------------------------------------------------------------
# Intent alignment
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", list(SearchMode))
@pytest.mark.parametrize("intent", list(PlayIntent))
def test_every_one_of_the_six_cells_is_readable(
    mode: SearchMode, intent: PlayIntent
) -> None:
    """Two modes by three declarations, and no combination falls through."""

    reading = intent_alignment(
        searcher(mode=mode),
        candidate(declared_intent=intent.value),
        LIVE_RULESET.intent,
    )
    assert reading is not None
    assert isinstance(reading.evidence, IntentAlignmentEvidence)
    assert reading.evidence.their_intent == intent.value
    assert reading.evidence.my_mode is mode


def test_silence_stands_the_term_down_and_opposition_costs_the_whole_weight() -> None:
    """Silence and opposition are different, and opposition costs strictly more.

    Not declaring drops the term and renormalises its weight onto the others, so
    it costs nothing. Declaring the opposite reads the table's zero and loses the
    whole weight — which is why the *intent opposed* modifier is deleted rather
    than deferred: a second charge for a fact the term already scores at nought
    is a gate wearing a modifier's clothes.
    """

    silent = intent_alignment(searcher(), candidate(), LIVE_RULESET.intent)
    opposed = intent_alignment(
        searcher(),
        candidate(declared_intent=PlayIntent.FOR_FUN.value),
        LIVE_RULESET.intent,
    )
    assert silent == StoodDown(
        term=Term.INTENT_ALIGNMENT, reason=DegradedReason.NOTHING_FROM_THEM
    )
    assert isinstance(opposed, TermReading)
    assert opposed.value == 0.0
    assert isinstance(opposed.evidence, IntentAlignmentEvidence)
    assert opposed.evidence.aligned is False


def test_no_preference_is_nearly_as_good_as_a_match_in_both_modes() -> None:
    """These players are the glue, and punishing the honest middle would teach
    everybody to declare a side."""

    for mode in SearchMode:
        reading = intent_alignment(
            searcher(mode=mode),
            candidate(declared_intent=PlayIntent.NO_PREFERENCE.value),
            LIVE_RULESET.intent,
        )
        assert reading is not None
        assert 0.8 <= reading.value < 1.0
        assert isinstance(reading.evidence, IntentAlignmentEvidence)
        # `aligned` is about the two declarations, never about the number: the
        # honest middle is *nearly* as good and is not the same evening.
        assert reading.evidence.aligned is False


def test_a_declaration_this_ruleset_cannot_price_is_a_refusal_and_not_a_guess() -> None:
    """A cell nobody wrote is a bug that shipped, not a candidate to score.

    Reading it as zero would bury every player who declared it; reading it as a
    stand-down would hide the release that forgot it.
    """

    with pytest.raises(InvariantViolated, match="does not price"):
        intent_alignment(
            searcher(),
            candidate(declared_intent="HERE_FOR_THE_BEER"),
            LIVE_RULESET.intent,
        )


# ---------------------------------------------------------------------------
# Reliability
# ---------------------------------------------------------------------------

FOUR_RATIOS = {
    ReliabilityStrand.SHOWS_UP: (90, 12),
    ReliabilityStrand.ANSWERS_CHALLENGES: (80, 9),
    ReliabilityStrand.KEEPS_PLANS: (60, 7),
    ReliabilityStrand.SETTLES_UP: (50, 6),
}


def test_no_record_at_all_stands_the_term_down() -> None:
    """**No record is not a bad record.** Not ``0.5``, not ``0`` — absent."""

    assert reliability(candidate(), COMP, LIVE_RULESET.reliability) == StoodDown(
        term=Term.RELIABILITY, reason=DegradedReason.NOTHING_FROM_THEM
    )


def test_a_strand_below_the_observation_bar_stands_down_alone() -> None:
    """One no-show out of one game is not thirty-five out of thirty-eight.

    The strand is **absent from the list** rather than present at zero, and the
    survivors renormalise inside the term: *we have not seen enough* and *they
    are bad at this* are different facts.
    """

    thin = {**FOUR_RATIOS, ReliabilityStrand.SETTLES_UP: (0, 1)}
    reading = reliability(
        candidate(reliability=record(ratios=thin)), COMP, LIVE_RULESET.reliability
    )
    assert isinstance(reading, TermReading)
    assert isinstance(reading.evidence, ReliabilityEvidence)
    named = {strand.strand for strand in reading.evidence.strands}
    assert ReliabilityStrand.SETTLES_UP not in named
    assert named == set(FOUR_RATIOS) - {ReliabilityStrand.SETTLES_UP}


def test_the_observation_bar_is_per_strand_and_only_one_of_them_asks_for_five(
) -> None:
    """**Per-strand minimums, at their boundary** (``docs/adr/0160``).

    The same four observations behind two strands: *shows up* is over its bar of
    three and reads, *answers about results* is under its bar of five and stands
    down alone. Raising a single number to five instead would have taken the
    first of those away too — which is a decision about how this product treats
    newcomers, and not a consequence of tuning one strand.
    """

    bars = LIVE_RULESET.reliability.min_observations
    assert bars[ReliabilityStrand.ANSWERS_RESULTS] == 5
    assert bars[ReliabilityStrand.SHOWS_UP] == 3

    thin = {
        ReliabilityStrand.SHOWS_UP: (90, 4),
        ReliabilityStrand.ANSWERS_RESULTS: (20, 4),
    }
    reading = reliability(
        candidate(reliability=record(ratios=thin)), COMP, LIVE_RULESET.reliability
    )
    assert isinstance(reading, TermReading)
    assert isinstance(reading.evidence, ReliabilityEvidence)
    assert {strand.strand for strand in reading.evidence.strands} == {
        ReliabilityStrand.SHOWS_UP
    }


def test_a_strand_at_its_own_bar_exactly_is_read() -> None:
    """The bar is *below it stands down*, so the bar itself counts.

    One observation either side of the number, on the one strand whose bar is not
    the others': four is nothing and five is a record.
    """

    bar = LIVE_RULESET.reliability.min_observations[
        ReliabilityStrand.ANSWERS_RESULTS
    ]

    def named(observations: int) -> set[ReliabilityStrand]:
        reading = reliability(
            candidate(
                reliability=record(
                    ratios={ReliabilityStrand.ANSWERS_RESULTS: (60, observations)}
                )
            ),
            COMP,
            LIVE_RULESET.reliability,
        )
        if isinstance(reading, StoodDown):
            return set()
        assert isinstance(reading.evidence, ReliabilityEvidence)
        return {strand.strand for strand in reading.evidence.strands}

    assert named(bar - 1) == set()
    assert named(bar) == {ReliabilityStrand.ANSWERS_RESULTS}


def test_a_record_past_the_horizon_stands_the_whole_term_down() -> None:
    """The strands share one cause — *this player stopped playing*."""

    horizon = LIVE_RULESET.reliability.horizon_days
    fresh = record(ratios=FOUR_RATIOS, days_since_last_observation=horizon)
    stale = record(ratios=FOUR_RATIOS, days_since_last_observation=horizon + 1)
    assert reliability(candidate(reliability=fresh), COMP, LIVE_RULESET.reliability)
    assert reliability(
        candidate(reliability=stale), COMP, LIVE_RULESET.reliability
    ) == StoodDown(term=Term.RELIABILITY, reason=DegradedReason.NOTHING_FROM_THEM)


def test_the_two_mode_vectors_order_the_same_two_candidates_oppositely() -> None:
    """The proof the decomposition earns its complexity, rather than the assertion.

    Two candidates identical on three strands, differing only on *answers about
    results* and *sportsmanship*. Competitive prefers one and for fun prefers the
    other — a single blended score cannot express that, and the decomposition is
    justified for exactly as long as such a pair exists.

    **The widest pair is back, and it is this one** (``docs/adr/0160``). It was
    *confirms results* against *sportsmanship* at 24/4 versus 5/16; that strand
    was struck (``docs/adr/0137``) and the inversion narrowed to *keeps plans*'s
    18/7 against 15/17, which still flipped and was what this test asserted.
    *Answers about results* enters at the share the struck name held, so the pair
    asserted here is 24/4 against 5/16 again. It is asserted rather than assumed
    because the day the last inverting pair leaves this vector is the day the
    whole decomposition stops paying for itself and should be argued again.
    """

    def reader(answers_results: int, sportsmanship: float) -> float:
        strands = {
            ReliabilityStrand.SHOWS_UP: (75, 20),
            ReliabilityStrand.ANSWERS_CHALLENGES: (75, 20),
            ReliabilityStrand.SETTLES_UP: (75, 20),
            ReliabilityStrand.ANSWERS_RESULTS: (answers_results, 20),
        }
        readings = [
            reliability(
                candidate(
                    reliability=record(
                        ratios=strands, sportsmanship=(sportsmanship, 20)
                    )
                ),
                rules,
                LIVE_RULESET.reliability,
            )
            for rules in (COMP, FUN)
        ]
        assert all(reading is not None for reading in readings)
        return readings  # type: ignore[return-value]

    p_comp, p_fun = reader(95, 3.2)
    q_comp, q_fun = reader(55, 4.8)
    assert p_comp.value > q_comp.value
    assert q_fun.value > p_fun.value


def test_sportsmanship_is_read_over_the_rating_scales_own_ends() -> None:
    """The one strand the engine derives, because it publishes no figure.

    A mean of 1 is the worst a player can be *rated*, which is a measurement and
    reads zero; a mean of 5 reads one. Anything else would be an invented origin.
    """

    only = {ReliabilityStrand.SPORTSMANSHIP}
    for mean, expected in ((1.0, 0.0), (3.0, 0.5), (5.0, 1.0)):
        reading = reliability(
            candidate(reliability=record(sportsmanship=(mean, 20))),
            COMP,
            LIVE_RULESET.reliability,
        )
        assert reading is not None
        assert reading.value == pytest.approx(expected)
        assert isinstance(reading.evidence, ReliabilityEvidence)
        assert {strand.strand for strand in reading.evidence.strands} == only


def test_the_evidence_carries_the_published_score_and_not_the_blend() -> None:
    """**The one deliberate place the matcher reads the blend instead of the strands.**

    A penalty justified by a figure that exists nowhere a human can look is
    unexplainable, and a player who works their visible score back up must be
    able to watch the penalty lift. So the number printed is the profile's, and
    the number weighed is the per-mode blend — and they differ here on purpose.
    """

    bar = LIVE_RULESET.reliability.published_score_bar
    reading = reliability(
        candidate(reliability=record(ratios=FOUR_RATIOS, published_score=bar - 1)),
        COMP,
        LIVE_RULESET.reliability,
    )
    assert reading is not None
    assert isinstance(reading.evidence, ReliabilityEvidence)
    assert reading.evidence.score == bar - 1
    assert reading.evidence.floor_breached is True
    assert reading.evidence.score != pytest.approx(reading.value * 100)


# ---------------------------------------------------------------------------
# Availability overlap
# ---------------------------------------------------------------------------


def test_the_denominator_is_the_searchers_own_slots() -> None:
    """*How much of my week does this person cover* — the glossary, verbatim.

    A candidate free all week covers all of a two-hour searcher's week, and a
    candidate free six hours covers six of a whole week's 112. The asymmetry is
    the point, and it is what makes the reading a fact about the pair.
    """

    week = cells(*[(day, hour) for day in range(1, 8) for hour in HOURS_OF_THE_DAY])
    narrow = availability_overlap(
        searcher(grid=cells((1, 19), (3, 19))),
        candidate(grid=week),
    )
    wide = availability_overlap(searcher(grid=week), candidate(grid=week[:6]))
    assert narrow is not None and wide is not None
    assert narrow.value == 1.0
    assert wide.value == pytest.approx(6 / 112)


@pytest.mark.parametrize(
    "side,reason",
    [
        ("searcher", DegradedReason.NOTHING_FROM_YOU),
        ("candidate", DegradedReason.NOTHING_FROM_THEM),
    ],
)
def test_a_blank_grid_on_either_side_stands_the_term_down(
    side: str, reason: DegradedReason
) -> None:
    """**Blank means we do not know**, and it is load-bearing twice.

    It is the only thing between the term and a division by zero, and scoring a
    cleared grid as ``0`` would be the invented zero the whole engine refuses:
    *you two never overlap* is a different claim from *nobody has said when they
    play*.

    **And it says whose blank it is**, because *you have not said when you play*
    is the only one of the two sentences the reader can act on.
    """

    blank: tuple = ()
    reading = availability_overlap(
        searcher(grid=blank) if side == "searcher" else searcher(),
        candidate(grid=blank) if side == "candidate" else candidate(),
    )
    assert reading == StoodDown(term=Term.AVAILABILITY_OVERLAP, reason=reason)


def test_two_blank_grids_name_the_searchers_own_side() -> None:
    """**The tie goes to the side the reader can do something about.**

    Both grids blank is one stand-down and two true sentences, and the product
    owes the searcher the one that is theirs to fix.
    """

    blank: tuple = ()
    assert availability_overlap(
        searcher(grid=blank), candidate(grid=blank)
    ) == StoodDown(
        term=Term.AVAILABILITY_OVERLAP, reason=DegradedReason.NOTHING_FROM_YOU
    )


def test_no_shared_cell_scores_the_measured_zero_instead() -> None:
    """Both weeks were read and they do not meet — which is a measurement."""

    reading = availability_overlap(
        searcher(grid=cells((1, 19))),
        candidate(grid=cells((2, 10))),
    )
    assert reading is not None
    assert reading.value == 0.0
    assert isinstance(reading.evidence, AvailabilityOverlapEvidence)
    assert reading.evidence.shared_count == 0
    assert reading.evidence.next_slot is None


def test_the_next_shared_slot_wraps_the_week_and_orders_inside_a_day() -> None:
    """Day resolution, and **the caller resolves today** — no date, no timezone.

    An hour on today's weekday is nought days away whatever the time is now: the
    week is a preference and not a promise, and the engine is told the day and
    never the clock. Inside a day the earlier hour comes first.
    """

    week = cells(
        (2, 19),
        (3, 19),
        (3, 10),
    )
    wednesday = availability_overlap(
        searcher(grid=week, today=iso_weekday(3)), candidate(grid=week)
    )
    thursday = availability_overlap(
        searcher(grid=week, today=iso_weekday(4)), candidate(grid=week)
    )
    assert wednesday is not None and thursday is not None
    assert isinstance(wednesday.evidence, AvailabilityOverlapEvidence)
    assert isinstance(thursday.evidence, AvailabilityOverlapEvidence)
    # Today, and ten before seven in the evening.
    assert wednesday.evidence.next_slot == SharedSlot(day=3, hour=10)
    # Tomorrow is nothing; the next is Tuesday, six days on.
    assert thursday.evidence.next_slot == SharedSlot(day=2, hour=19)


def test_the_availability_term_reads_no_constant_at_all() -> None:
    """Significance, staleness and proximity are struck and none returns hidden.

    The check is the ratio itself: every reading is ``|shared| / |mine|`` exactly,
    with no coefficient anywhere in it, so a searcher with three cells can only
    ever read four distinct values. Anything smuggled back in would break that.
    """

    grid = cells((1, 19), (3, 19), (5, 19))
    readings = []
    for shared in range(len(grid) + 1):
        reading = availability_overlap(
            searcher(grid=grid),
            candidate(grid=grid[:shared] + cells((7, 10))),
        )
        assert reading is not None
        readings.append(reading.value)
    assert readings == pytest.approx([0.0, 1 / 3, 2 / 3, 1.0])


# ---------------------------------------------------------------------------
# Distance
# ---------------------------------------------------------------------------


def test_distance_is_full_marks_inside_the_shoulder_and_zero_past_the_ring() -> None:
    """Both ends are fractions of **the searcher's own** ring.

    A ten kilometre searcher and a fifty kilometre one each said what far means
    to them, and a constant in kilometres would overrule one of them — so the two
    read identically at the same fraction of their own radius.
    """

    rules = LIVE_RULESET.distance
    for radius in (10.0, 50.0):
        inside = distance(
            searcher(radius_km=radius),
            candidate(distance_km=radius * rules.full_marks_within),
            rules,
        )
        at_zero = distance(
            searcher(radius_km=radius),
            candidate(distance_km=radius * rules.zero_at),
            rules,
        )
        at_the_ring = distance(
            searcher(radius_km=radius), candidate(distance_km=radius), rules
        )
        assert inside is not None and at_zero is not None and at_the_ring is not None
        # The shoulder is a limit, so it is asserted as one: a float that lands
        # a quadrillionth under one at exactly 0.70·r is the clamp doing nothing,
        # not the curve disagreeing.
        assert inside.value == pytest.approx(1.0)
        assert at_zero.value == 0.0
        # The hard cut at the ring is a gate; a curve reaching zero there would
        # charge for it twice.
        assert at_the_ring.value == pytest.approx(1 / 3, abs=1e-3)


def test_distance_prints_whole_kilometres_and_the_coarse_area() -> None:
    """The finest location fact that has ever crossed the fence is an area code."""

    reading = distance(
        searcher(),
        candidate(distance_km=9.25, area_code="PL-WAW-N"),
        LIVE_RULESET.distance,
    )
    assert reading is not None
    assert isinstance(reading.evidence, DistanceEvidence)
    assert reading.evidence.km == 9
    assert reading.evidence.area_code == "PL-WAW-N"


# ---------------------------------------------------------------------------
# The two tag terms
# ---------------------------------------------------------------------------

ON_COURT = (SocialTag.PLAYS_TO_WIN.value, SocialTag.QUIET_AND_FOCUSED.value)
AFTERWARDS = (SocialTag.STAYS_FOR_A_DRINK.value, SocialTag.HERE_TO_COMPETE.value)


def test_a_column_stands_down_when_either_side_holds_no_tag_in_its_domain() -> None:
    """*They said nothing about the hour on court* is not *nothing fired*.

    The domain is derived from the matrix rather than declared, so it re-derives
    itself the moment product edits a row.
    """

    silent_on_court = playing_style(
        searcher(tags=AFTERWARDS),
        candidate(tags=AFTERWARDS),
        Seat.OPPONENT,
        LIVE_RULESET.tags,
    )
    # Neither side is tagged for the hour on court, and the searcher's own side
    # is the one named: the tie goes to the half the reader can act on.
    assert silent_on_court == StoodDown(
        term=Term.PLAYING_STYLE, reason=DegradedReason.NOTHING_FROM_YOU
    )
    # And the other column, over the same two people, is a reading.
    assert isinstance(
        social_vibe(
            searcher(tags=AFTERWARDS),
            candidate(tags=AFTERWARDS),
            Seat.OPPONENT,
            LIVE_RULESET.tags,
        ),
        TermReading,
    )


def test_a_column_names_their_side_when_only_theirs_is_untagged() -> None:
    """One tagged side and one bare one is *their* gap, and it says so.

    The two sentences are not interchangeable: one asks the searcher to finish
    their own profile, and the other explains why a card is thinner than the one
    beside it.
    """

    assert playing_style(
        searcher(tags=ON_COURT),
        candidate(tags=AFTERWARDS),
        Seat.OPPONENT,
        LIVE_RULESET.tags,
    ) == StoodDown(term=Term.PLAYING_STYLE, reason=DegradedReason.NOTHING_FROM_THEM)


def test_a_tag_about_the_person_may_be_shown_and_may_never_score() -> None:
    """``OPEN_TO_MEET_SOMEONE`` takes no row of any kind, so it is in no domain.

    A player who spends one of their minimum two tags on it has spent half their
    budget on something the matcher never reads — a price the record accepts
    rather than solves, and one this test is what makes true.
    """

    only_the_person = (SocialTag.OPEN_TO_MEET_SOMEONE.value,)
    named = {
        tag for row in LIVE_RULESET.tags.relationship_matrix for tag in (row.a, row.b)
    }
    assert SocialTag.OPEN_TO_MEET_SOMEONE.value not in named
    for column, term in (
        (playing_style, Term.PLAYING_STYLE),
        (social_vibe, Term.SOCIAL_VIBE),
    ):
        assert column(
            searcher(tags=only_the_person),
            candidate(tags=only_the_person),
            Seat.OPPONENT,
            LIVE_RULESET.tags,
        ) == StoodDown(term=term, reason=DegradedReason.NOTHING_FROM_YOU)


def test_nothing_firing_is_the_measured_zero_and_a_capped_clash_is_the_real_one() -> (
    None
):
    """**The term's zero is a real clash, not an absence of relationship.**

    Scored the other way, *"you two clash badly"* is numerically identical to
    *"you two share nothing"* — and two random four-tag draws from nineteen
    overlap under once on average, so the typical pair would sit at the bottom of
    a term carrying a quarter of a friendly.
    """

    cap = LIVE_RULESET.tags.clash_cap
    nothing = playing_style(
        searcher(tags=(SocialTag.PLAYS_TO_WIN.value,)),
        candidate(tags=(SocialTag.WARMS_UP_PROPERLY.value,)),
        Seat.OPPONENT,
        LIVE_RULESET.tags,
    )
    assert nothing is not None
    assert nothing.value == pytest.approx(cap / (1 + cap))
    assert nothing.value == pytest.approx(0.20)
    assert isinstance(nothing.evidence, PlayingStyleEvidence)
    assert nothing.evidence.matched == ()
    assert nothing.evidence.complementary == ()
    assert nothing.evidence.clashing == ()


def test_a_shared_tag_may_pay_both_a_match_and_a_complement() -> None:
    """Two different claims: *you both want this*, and *your two things fit*.

    Refusing the second would delete the complement rows for exactly the pairs
    they describe best — ``HERE_TO_IMPROVE`` beside ``WARMS_UP_PROPERLY`` is one
    person wanting to get better and the other running the half hour that does it,
    and both of them holding both tags does not make that less true.
    """

    both = (SocialTag.HERE_TO_IMPROVE.value, SocialTag.WARMS_UP_PROPERLY.value)
    reading = playing_style(
        searcher(tags=both), candidate(tags=both), Seat.OPPONENT, LIVE_RULESET.tags
    )
    assert reading is not None
    assert isinstance(reading.evidence, PlayingStyleEvidence)
    assert SocialTag.WARMS_UP_PROPERLY.value in reading.evidence.matched
    assert reading.evidence.complementary != ()


def test_an_unseated_pair_reads_the_opponent_row_and_a_partner_row_does_not_fire() -> (
    None
):
    """The forgiving reading is the default; the harsh one waits for a seat.

    *Talks through the match* against *quiet and focused* is two rows with
    disjoint seat scope — Real as partners, Mild as opponents — which is how *far
    worse as partners* is said without inventing a second severity field. Being
    wrong about a clash buries a person, so the unseated shortlist takes the
    milder row.
    """

    talker = (SocialTag.TALKS_THROUGH_THE_MATCH.value,)
    quiet = (SocialTag.QUIET_AND_FOCUSED.value,)
    as_opponents = playing_style(
        searcher(tags=talker), candidate(tags=quiet), Seat.OPPONENT, LIVE_RULESET.tags
    )
    as_partners = playing_style(
        searcher(tags=talker), candidate(tags=quiet), Seat.PARTNER, LIVE_RULESET.tags
    )
    assert as_opponents is not None and as_partners is not None
    assert as_partners.value < as_opponents.value


def test_a_row_scoped_to_one_mode_does_not_fire_in_the_other() -> None:
    """*That is precisely how you improve* in a counted game, and a clash in a
    friendly — the same two ids, two disjoint rows, opposite signs."""

    a = (SocialTag.HERE_TO_IMPROVE.value,)
    b = (SocialTag.PLAYS_TO_WIN.value,)
    competitive = playing_style(
        searcher(tags=a, mode=SearchMode.COMPETITIVE),
        candidate(tags=b),
        Seat.OPPONENT,
        LIVE_RULESET.tags,
    )
    friendly = playing_style(
        searcher(tags=a, mode=SearchMode.FOR_FUN),
        candidate(tags=b),
        Seat.OPPONENT,
        LIVE_RULESET.tags,
    )
    assert competitive is not None and friendly is not None
    assert isinstance(competitive.evidence, PlayingStyleEvidence)
    assert isinstance(friendly.evidence, PlayingStyleEvidence)
    assert competitive.evidence.complementary != ()
    assert competitive.evidence.clashing == ()
    assert friendly.evidence.complementary == ()
    assert friendly.evidence.clashing != ()


def test_the_clash_arm_is_capped_so_no_stack_of_them_buries_anybody() -> None:
    """Being wrong about a match costs a duller evening; being wrong about a
    clash buries a person, and the magnitudes are asymmetric because the costs are.

    Driven against a ruleset with a wall of clash rows rather than against the
    shipped seven, because the cap's whole job is to bind on a matrix nobody has
    authored yet.
    """

    ids = [tag.value for tag in SocialTag][:8]
    piled = dataclasses.replace(
        LIVE_RULESET.tags,
        relationship_matrix=tuple(
            TagRelationship(
                a=ids[index],
                b=ids[index + 1],
                kind=TagRelationshipKind.CLASH,
                column=TagColumn.STYLE,
                modes=tuple(SearchMode),
                seats=tuple(Seat),
                severity=ClashSeverity.REAL,
            )
            for index in range(0, len(ids) - 1, 2)
        ),
    )
    reading = playing_style(
        searcher(tags=tuple(ids)), candidate(tags=tuple(ids)), Seat.OPPONENT, piled
    )
    assert reading is not None
    assert reading.value == 0.0
    assert isinstance(reading.evidence, PlayingStyleEvidence)
    # Capped, and every row that fired is still named: the cap bounds the charge
    # and never the explanation.
    assert len(reading.evidence.clashing) == 4


def test_the_two_columns_are_two_variants_and_never_one_with_a_field() -> None:
    """A client dispatches over a type rather than branching on a value."""

    tags = (SocialTag.PLAYS_TO_WIN.value, SocialTag.HERE_TO_COMPETE.value)
    style = playing_style(
        searcher(tags=tags), candidate(tags=tags), Seat.OPPONENT, LIVE_RULESET.tags
    )
    vibe = social_vibe(
        searcher(tags=tags), candidate(tags=tags), Seat.OPPONENT, LIVE_RULESET.tags
    )
    assert style is not None and vibe is not None
    assert isinstance(style.evidence, PlayingStyleEvidence)
    assert isinstance(vibe.evidence, SocialVibeEvidence)


# ---------------------------------------------------------------------------
# The set of terms itself
# ---------------------------------------------------------------------------


def test_every_term_of_fit_is_read_and_each_answers_under_its_own_kind() -> None:
    """A term missing from the read would renormalise its weight away in silence.

    Which is the failure that makes a Fit uninterpretable rather than merely
    wrong: the number still adds up, and nothing anywhere says a term stopped
    being asked.
    """

    outcomes = read_terms(
        searcher(tags=(SocialTag.PLAYS_TO_WIN.value, SocialTag.HERE_TO_COMPETE.value)),
        candidate(
            tags=(SocialTag.PLAYS_TO_WIN.value, SocialTag.HERE_TO_COMPETE.value),
            declared_intent=PlayIntent.COMPETITIVE.value,
            reliability=record(ratios=FOUR_RATIOS),
        ),
        LIVE_RULESET,
        Seat.OPPONENT,
    )
    assert len(outcomes) == len(Term)
    for term, outcome in zip(Term, outcomes, strict=True):
        assert outcome is not None, f"{term.value} stood down on a full reading"
        assert outcome.term is term
        assert outcome.evidence.kind is term.evidence_kind


def test_a_reading_may_not_carry_another_terms_evidence() -> None:
    """The mistake is invisible on the wire: the breakdown still adds up, and one
    card silently explains its availability under the heading of its level."""

    with pytest.raises(InvariantViolated, match="emitted"):
        TermReading(
            term=Term.LEVEL_FIT,
            value=1.0,
            evidence=DistanceEvidence(km=1, area_code="X", outside_their_radius=False),
        )


def test_a_grid_cell_ticked_twice_is_refused_rather_than_folded() -> None:
    """The fold has an owner on the other side of the fence.

    A duplicate arriving here means that fold did not run — and the availability
    term would then divide by an inflated denominator and report *less* overlap
    than the pair has, which is a wrong answer rather than a loud one.
    """

    twice = cells((1, 19)) * 2
    with pytest.raises(InvariantViolated, match="ticked twice"):
        searcher(grid=twice)


@pytest.mark.parametrize("hour", [-1, 24, True])
def test_a_grid_cell_outside_the_day_is_a_broken_precondition(hour) -> None:
    """The engine checks an hour is an hour of a day and nothing narrower: which
    hours a player may tick is the Player profile's rule, not a second copy of it
    held here."""

    with pytest.raises(InvariantViolated, match="outside the day"):
        GridCell(day=iso_weekday(1), hour=hour)
