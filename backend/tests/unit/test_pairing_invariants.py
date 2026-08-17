"""What must still be true after any constant retune.

The opposite file to ``test_pairing_personas.py``. Nothing here reads a literal
that a constant owns: every assertion is either structural — the percentage and
the bar are one number viewed twice — or it reads the constant it is about. A
retune that breaks one of these has broken the model, not the baseline.
"""

import ast
import itertools
from dataclasses import dataclass, replace
from pathlib import Path
from typing import final

import pytest

from app.engines.forecast import (
    BalanceForecast,
    BalanceForecastEngine,
    Certainty,
    PairingAnalysis,
    SidesNotFormed,
    Split,
)
from app.engines.matchmaking import (
    MatchSnapshot,
    PlayerRef,
    PlayerSkill,
    SeatSnapshot,
)
from app.engines.pairing.core import (
    SPLITS,
    Side,
    absolute_gap_deviation,
    as_float,
    combine_uncertainty,
    expected_absolute_gap,
    round_half_away_from_zero,
    side_of_two,
)
from app.engines.pairing.v1 import (
    CONSTANTS,
    ENGINE_VERSION,
    PAIRED_SPORTS,
    PairingEngineV1,
)
from app.engines.pairing.v1.constants import PairingConstants
from app.kernel import SPORT_SPECS, Err, InvariantViolated, Ok, Sport, ratio
from tests.unit.matchmaking_snapshots import NOW, doubles, singles, skill

ROOT = Path(__file__).resolve().parents[2]
PAIRING = ROOT / "app" / "engines" / "pairing"

ENGINE = PairingEngineV1()

#: A spread of rosters wide enough to cross every branch: dead level, a hair
#: apart, half a level, past the clamp, and each of those at four Uncertainties
#: from certain to the onboarding floor. Written out rather than drawn at random,
#: because an invariant that only holds for the inputs a seed happened to pick is
#: not an invariant.
ROSTERS = tuple(
    (300, 300 + apart, sigma, other)
    for apart in (0, 5, 20, 50, 100, 130, 170, 250)
    for sigma in (0, 10, 35, 84)
    for other in (0, 20, 84)
)

#: The same spread at four seats. **Every invariant below is asserted over both**
#: — the doubles path adds a pairing decision and a weighted team strength in
#: front of the arithmetic, and none of them is licence for a card to contradict
#: itself. Rosters are built so that the four Levels straddle rather than
#: ascend, which is what makes the three splits genuinely different from each
#: other rather than three orderings of the same near-tie.
DOUBLES_ROSTERS = tuple(
    (
        (300, sigma),
        (300 + apart, other),
        (max(100, 300 - apart), other),
        (min(500, 300 + 2 * apart), sigma),
    )
    for apart in (0, 5, 20, 50, 90, 130)
    for sigma in (0, 15, 84)
    for other in (0, 35, 120)
)


def forecast_of(
    level_a: int, level_b: int, sigma_a: int, sigma_b: int
) -> BalanceForecast:
    """The forecast for one roster, through the Protocol and nothing else."""

    snapshot = singles(skill("a", level_a, sigma_a), skill("b", level_b, sigma_b))
    result = ENGINE.analyse(snapshot=snapshot, now=NOW)
    assert isinstance(result.forecast, Ok)
    return result.forecast.value


def analysis_of(*roster, viewer=None, sport=Sport.PADEL) -> PairingAnalysis:
    """The whole analysis for a four-player roster, through the Protocol."""

    players = [skill(NAMES[seat], *rating) for seat, rating in enumerate(roster)]
    snapshot = doubles(*players, sport=sport, viewer=viewer)
    return ENGINE.analyse(snapshot=snapshot, now=NOW)


def doubles_forecast_of(*roster: tuple[int, int]) -> BalanceForecast:
    """The *chosen* split's forecast — the one number a card would show."""

    result = analysis_of(*roster).forecast
    assert isinstance(result, Ok)
    return result.value


#: Seat names, so an assertion about who ended up with whom reads as people.
NAMES = ("ada", "bo", "cy", "dee")


@pytest.fixture(scope="module")
def every_forecast() -> tuple[BalanceForecast, ...]:
    """Every forecast this engine can produce, at both arities.

    One collection, so that the invariants below are literally the same
    assertions over singles and doubles rather than two files' worth that can
    drift apart.
    """

    return tuple(forecast_of(*roster) for roster in ROSTERS) + tuple(
        doubles_forecast_of(*roster) for roster in DOUBLES_ROSTERS
    )


def test_the_invariants_below_are_asserted_over_both_arities(every_forecast):
    """A sweep that has quietly lost half its inputs passes by finding nothing.

    The doubles path is the one this slice adds, so it is the one that could be
    dropped from the fixture and leave every assertion below green.
    """

    assert len(every_forecast) == len(ROSTERS) + len(DOUBLES_ROSTERS)
    assert len(DOUBLES_ROSTERS) >= 40, len(DOUBLES_ROSTERS)


# --- The identity between the percentage and the bar ----------------------------


def test_the_percentage_and_the_split_bar_satisfy_their_identity(every_forecast):
    """The bar is a *rendering* of the percentage, not a second opinion.

    The underdog holds half the balance percentage, and the two shares hold the
    whole bar between them. No correction term, for any input — which is what
    stops a card printing a floored number beside an unfloored picture.
    """

    for forecast in every_forecast:
        assert forecast.underdog_share == forecast.estimate // 2
        assert forecast.favourite_share + forecast.underdog_share == 100
        assert forecast.favourite_share >= forecast.underdog_share


def test_the_bar_is_derived_from_the_rounded_percentage_and_not_beside_it(
    every_forecast,
):
    """Round once. Both shares are functions of the integer estimate alone, so
    there is no second rounding for the two to disagree in."""

    for forecast in every_forecast:
        assert forecast.underdog_share == forecast.estimate // 2
        assert forecast.favourite_share == 100 - forecast.estimate // 2


def test_the_floor_and_the_cap_saturate_at_the_same_instant(every_forecast):
    """The failure this whole derivation exists to make unwritable: two clamps
    binding at two different gaps, printing the floored percentage beside a bar
    that has not reached its cap."""

    for forecast in every_forecast:
        assert forecast.estimate >= CONSTANTS.balance_floor
        assert forecast.estimate <= 100
        assert forecast.favourite_share <= CONSTANTS.favourite_cap
        floored = forecast.estimate == CONSTANTS.balance_floor
        capped = forecast.favourite_share == CONSTANTS.favourite_cap
        assert floored == capped


def test_the_floor_and_the_cap_are_derived_from_the_one_clamped_quantity():
    """Neither is written down. Retune the clamp and both move together."""

    exact = 100 - CONSTANTS.gap_coefficient * CONSTANTS.gap_clamp
    assert CONSTANTS.balance_floor == exact
    assert CONSTANTS.favourite_cap == 100 - CONSTANTS.balance_floor // 2


def test_a_balance_floor_that_is_not_a_whole_percent_is_refused():
    """A floor of 34,5% would be a number no card can print, and half a point of
    drift between the percentage and the bar derived from it."""

    with pytest.raises(InvariantViolated, match="not a whole percent"):
        assert replace(CONSTANTS, gap_clamp=ratio(131, 100)).balance_floor


# --- The weighting constant, and the two ways a retune could invert it ---------------


def test_the_weighting_covers_exactly_the_sports_that_have_a_pairing():
    """Read off the kernel registry rather than listed, so a fifth sport played
    by four cannot be added without either a weight or a build failure."""

    assert set(CONSTANTS.weaker_partner_weight) == PAIRED_SPORTS
    assert PAIRED_SPORTS == {Sport.PADEL, Sport.BADMINTON}
    assert all(
        spec.players == 4
        for sport, spec in SPORT_SPECS.items()
        if sport in PAIRED_SPORTS
    )


def test_both_sports_carry_the_same_weight_at_v1_and_each_can_move_alone():
    """*Is a padel partnership more forgiving than a badminton one?* is a
    question for measurement. The point of the mapping is that answering it is a
    constant change rather than a rewrite, so the two are checked to be
    separable, not merely equal."""

    padel, badminton = (
        CONSTANTS.weaker_partner_weight[sport]
        for sport in (Sport.PADEL, Sport.BADMINTON)
    )
    assert padel == badminton

    retuned = replace(
        CONSTANTS,
        weaker_partner_weight={Sport.PADEL: ratio(70, 100), Sport.BADMINTON: badminton},
    )
    assert retuned.weaker_partner_weight[Sport.BADMINTON] == badminton


@pytest.mark.parametrize("weight", [ratio(50, 100), ratio(45, 100), ratio(0, 100)])
def test_a_weight_that_does_not_favour_the_weaker_partner_is_refused(weight):
    """At or below a half this is not a weaker-partner weighting; it is the model
    inverted, with every percentage it produces still looking plausible."""

    with pytest.raises(InvariantViolated, match="does not weight the weaker partner"):
        replace(
            CONSTANTS,
            weaker_partner_weight={
                Sport.PADEL: weight,
                Sport.BADMINTON: ratio(55, 100),
            },
        )


def test_a_paired_sport_left_without_a_weight_is_refused_when_the_constants_are_built():
    """At import, over the whole map — louder than one home screen failing."""

    with pytest.raises(InvariantViolated, match="the registry pairs"):
        replace(CONSTANTS, weaker_partner_weight={Sport.PADEL: ratio(55, 100)})


# --- The gap, and the one clamp on it -------------------------------------------


def test_the_reported_gap_is_never_below_the_absolute_expected_gap(every_forecast):
    """``E|X|`` and not ``|E X|``. Uncertainty inflates the gap; it can never be
    reported as a confident near-zero."""

    for forecast in every_forecast:
        assert (
            forecast.expected_gap
            >= abs(as_float(forecast.side_a) - as_float(forecast.side_b)) - 1e-12
        )


def test_uncertainty_only_ever_widens_the_expected_gap():
    for mean in (0.0, 0.2, 0.5, 1.3, 2.0):
        widening = [
            expected_absolute_gap(mean, spread) for spread in (0.0, 0.1, 0.4, 1.2)
        ]
        assert widening == sorted(widening)
        assert widening[0] == pytest.approx(abs(mean))


def test_the_gap_is_the_only_quantity_that_is_clamped():
    """The percentage saturates; the gap the caller is handed does not.

    A caller ranking two mismatches still needs to know that one of them is
    worse, and a clamped field would make the two indistinguishable — as well as
    breaking *the reported gap is never below the absolute expected gap* at the
    top of the scale.
    """

    forecast = forecast_of(250, 500, 0, 0)
    assert forecast.estimate == CONSTANTS.balance_floor
    assert forecast.expected_gap > as_float(CONSTANTS.gap_clamp)


def test_beyond_scale_distinguishes_a_mismatch_from_a_floored_percentage():
    """Both print the floor. Only one of them means the scale ran out."""

    floored = forecast_of(300, 430, 0, 0)
    mismatch = forecast_of(300, 500, 0, 0)
    assert floored.estimate == mismatch.estimate == CONSTANTS.balance_floor
    assert floored.beyond_scale is False
    assert mismatch.beyond_scale is True


def test_the_percentage_is_rounded_half_away_from_zero_and_not_half_to_even():
    """The rule Python's built-in ``round`` does not implement.

    3,00 against 3,35 lands on exactly 82,5, and half-to-even sends it *down* to
    82 while sending its neighbours up — two forecasts a hundredth of a Level
    apart rounded in opposite directions, for no reason a player could be told.
    Away from zero is symmetric in sign and always the same direction for the
    same magnitude.
    """

    assert forecast_of(300, 335, 0, 0).estimate == 83
    assert round(82.5) == 82

    assert round_half_away_from_zero(82.5) == 83
    assert round_half_away_from_zero(83.5) == 84
    assert round_half_away_from_zero(-2.5) == -3
    assert round_half_away_from_zero(2.4999) == 2


def test_a_certain_roster_reports_the_gap_anybody_can_do_by_hand(every_forecast):
    """At zero Uncertainty the expectation collapses to the difference itself,
    which is the one case the arithmetic can be checked against mental arithmetic
    rather than against itself."""

    assert forecast_of(300, 350, 0, 0).expected_gap == pytest.approx(0.50)
    assert absolute_gap_deviation(0.5, 0.0) == 0.0


# --- The margin, and the grade of it --------------------------------------------


def test_there_is_no_separate_uncertainty_penalty(every_forecast):
    """The estimate is a function of the reported gap and nothing else.

    The source design subtracted a spread term from the percentage *after*
    computing it, which made the bar and the number two opinions and needed a
    correction to reconcile. Here uncertainty reaches the percentage only by
    widening the gap, so this reconstruction — from the reported gap, the clamp
    and the coefficient — has to reproduce the estimate exactly, for every
    roster. Anything subtracted on the way out would show up here as a constant
    offset.
    """

    clamp = as_float(CONSTANTS.gap_clamp)
    coefficient = as_float(CONSTANTS.gap_coefficient)
    for forecast in every_forecast:
        from_the_gap = round_half_away_from_zero(
            100.0 - coefficient * min(forecast.expected_gap, clamp)
        )
        assert forecast.estimate == from_the_gap


def test_the_margin_is_zero_exactly_when_the_platform_is_certain(every_forecast):
    for forecast in every_forecast:
        assert forecast.margin >= 0
    assert forecast_of(300, 350, 0, 0).margin == 0


def test_certainty_is_graded_from_the_margin_and_nothing_else(every_forecast):
    for forecast in every_forecast:
        if forecast.margin <= CONSTANTS.certain_margin:
            assert forecast.certainty is Certainty.HIGH
        elif forecast.margin <= CONSTANTS.unsure_margin:
            assert forecast.certainty is Certainty.MODERATE
        else:
            assert forecast.certainty is Certainty.LOW


def test_fit_to_print_reads_the_grade_rather_than_holding_its_own_copy(every_forecast):
    """Suppression is presentation. It is a property and not a field so that it
    cannot drift from the grade — and the estimate ranks either way."""

    for forecast in every_forecast:
        assert forecast.fit_to_print is (forecast.certainty is not Certainty.LOW)


def test_a_wider_uncertainty_never_raises_certainty():
    grades = [Certainty.HIGH, Certainty.MODERATE, Certainty.LOW]
    for level_b in (300, 320, 400):
        seen = [
            grades.index(forecast_of(300, level_b, sigma, sigma).certainty)
            for sigma in (0, 5, 15, 35, 60, 84, 120)
        ]
        assert seen == sorted(seen)


# --- No forecast, and why ---------------------------------------------------------


def test_a_seat_with_nobody_on_it_declines_rather_than_guessing():
    ada = skill("ada", 300, 20)
    empty = MatchSnapshot(
        sport=Sport.TENNIS,
        seats=(SeatSnapshot(ada), SeatSnapshot()),
        current_player=ada,
    )
    result = ENGINE.analyse(snapshot=empty, now=NOW).forecast
    assert isinstance(result, Err)
    assert result.reason == SidesNotFormed(sport="TENNIS", seated=1, sold=2)


def test_the_reason_is_a_machine_code_and_payload_never_a_sentence():
    """The clients own the words: a reason crosses the wire as ``{kind, …}``."""

    reason = SidesNotFormed(sport="PADEL", seated=4, sold=4)
    assert reason.kind == "sides_not_formed"
    assert not any(
        isinstance(value, str) and " " in value for value in vars(reason).values()
    )


def test_a_four_seat_sport_with_a_seat_open_declines_with_the_same_reason():
    """The assertion this test used to make was that a *full* padel court also
    declined, because no version had enumerated the three splits yet. It does
    not any more — that is this slice — and what survives is the half that was
    never about arity: a seat with nobody on it has nobody to put on a side.
    Imputation is the next slice; until then the engine declines.
    """

    seated = [skill(str(i), 300 + 10 * i, 20) for i in range(3)]
    result = ENGINE.analyse(snapshot=doubles(*seated, None), now=NOW).forecast
    assert isinstance(result, Err)
    assert result.reason.kind == "sides_not_formed"
    assert (result.reason.seated, result.reason.sold) == (3, 4)


@final
@dataclass(frozen=True)
class _SixSeatSport:
    """What a registry gaining a six-player sport would look like to the engine.

    Structural, and it has to be: ``MatchSnapshot`` reads its arity from the
    kernel registry and refuses a seat count that disagrees with it, which is
    exactly the guarantee that makes this case unreachable through the real
    vocabulary. The engine has a pairing rule for two seats and for four, and
    what it does about a third arity is a decision — it declines, so a sport
    added without a pairing rule produces no forecast rather than a wrong one on
    a home screen.
    """

    sport: Sport
    occupants: tuple[PlayerSkill, ...]
    current_player: PlayerSkill
    sold_seats: int = 6


def test_an_arity_this_version_has_no_pairing_rule_for_declines():
    roster = tuple(skill(str(seat), 300 + 10 * seat, 20) for seat in range(6))
    snapshot = _SixSeatSport(
        sport=Sport.PADEL, occupants=roster, current_player=roster[0]
    )
    result = ENGINE.analyse(snapshot=snapshot, now=NOW).forecast
    assert isinstance(result, Err)
    assert (result.reason.seated, result.reason.sold) == (6, 6)


# --- The three splits ---------------------------------------------------------------


def test_four_players_admit_exactly_three_splits_and_the_engine_returns_them_all():
    """The complete enumeration, derived here from scratch rather than read off
    the list it is checking. There is no fourth arrangement to miss."""

    every_partition = {
        frozenset({frozenset(left), frozenset(set(range(4)) - set(left))})
        for left in itertools.combinations(range(4), 2)
    }
    enumerated = {
        frozenset({frozenset(left), frozenset(right)}) for left, right in SPLITS
    }
    assert enumerated == every_partition
    assert len(SPLITS) == 3

    analysis = analysis_of((300, 20), (340, 20), (310, 20), (360, 20))
    assert len(analysis.splits) == 3


def test_every_split_seats_every_player_exactly_once():
    analysis = analysis_of((271, 15), (280, 20), (264, 25), (292, 18))
    for option in analysis.splits:
        assert len(option.side_a) == len(option.side_b) == 2
        assert sorted(option.side_a + option.side_b) == sorted(NAMES)


def test_the_three_splits_returned_are_three_different_arrangements():
    """Ranked, not sampled: all three are there and no two are the same one."""

    analysis = analysis_of((271, 15), (280, 20), (264, 25), (292, 18))
    arrangements = {
        frozenset({frozenset(option.side_a), frozenset(option.side_b)})
        for option in analysis.splits
    }
    assert len(arrangements) == 3


def test_the_splits_are_ranked_on_the_expected_gap_best_first():
    for roster in DOUBLES_ROSTERS:
        gaps = [option.forecast.expected_gap for option in analysis_of(*roster).splits]
        assert gaps == sorted(gaps), roster


def test_the_headline_forecast_is_the_winning_split_and_not_a_second_opinion():
    """One conclusion, shown twice. A card saying *you and Dee against Bo and Cy,
    76% balanced* cannot pair a forecast with an arrangement it was not computed
    from, because they are the same object."""

    for roster in DOUBLES_ROSTERS:
        analysis = analysis_of(*roster)
        assert isinstance(analysis.forecast, Ok)
        assert analysis.forecast.value is analysis.splits[0].forecast, roster


def test_no_other_split_would_have_scored_better_than_the_one_chosen():
    for roster in DOUBLES_ROSTERS:
        analysis = analysis_of(*roster)
        estimates = [option.forecast.estimate for option in analysis.splits]
        assert estimates[0] == max(estimates), roster


def test_a_split_is_chosen_on_the_expected_gap_and_not_on_the_paper_gap():
    """The selection bias that grows with Uncertainty, and the one case that
    shows it.

    Ada, Bo and Cy are known exactly; Dee answered a questionnaire yesterday and
    nothing else. Pairing Dee with Ada — the weakest of the three — makes Dee the
    *stronger* partner, so Dee's Uncertainty is carried at the lower weight; the
    arrangement whose two paper strengths are closest is the one where it is
    carried at the higher. So the engine chooses the split whose paper gap is
    seven times wider, and it is right to: the other split is not more even, it
    is merely less knowable, and its forecast comes back too uncertain to print
    while the chosen one prints.

    Ranking on the gap between the two strengths would take the flattering one
    every time, and would do so most often on exactly the rosters the platform
    knows least about.
    """

    analysis = analysis_of((300, 0), (320, 0), (340, 0), (310, 120))
    chosen, *rest = analysis.splits

    def paper_gap(option: Split) -> float:
        return abs(as_float(option.forecast.side_a) - as_float(option.forecast.side_b))

    assert set(chosen.side_a) == {"ada", "dee"}
    assert paper_gap(chosen) == pytest.approx(0.245)
    assert min(paper_gap(option) for option in rest) == pytest.approx(0.035)
    assert chosen.forecast.expected_gap < min(o.forecast.expected_gap for o in rest)
    assert chosen.forecast.fit_to_print is True
    assert all(option.forecast.fit_to_print is False for option in rest)


def test_ties_between_splits_keep_the_enumeration_order():
    """Four identical players make the three arrangements genuinely the same
    match. The sort is stable, so the answer is reproducible rather than
    whatever the last comparison happened to leave behind."""

    analysis = analysis_of(*[(300, 20)] * 4)
    gaps = {option.forecast.expected_gap for option in analysis.splits}
    assert len(gaps) == 1
    assert [option.side_a for option in analysis.splits] == [
        ("ada", "bo"),
        ("ada", "cy"),
        ("ada", "dee"),
    ]


def test_singles_carries_no_splits_at_all():
    """Singles has no pairing. An empty tuple says that; a one-element list would
    imply an election nobody can make."""

    analysis = ENGINE.analyse(
        snapshot=singles(skill("ada", 300, 20), skill("bo", 340, 20)), now=NOW
    )
    assert analysis.splits == ()


def test_a_declined_analysis_carries_no_splits_either():
    half_empty = doubles(skill("ada", 300, 20), skill("bo", 320, 20), None, None)
    analysis = ENGINE.analyse(snapshot=half_empty, now=NOW)
    assert isinstance(analysis.forecast, Err)
    assert analysis.splits == ()


def test_the_current_player_is_on_the_first_side_of_every_split():
    """Not only of the winner. A player reading the two arrangements they did not
    get needs *your side* to mean the same thing in all three."""

    for seat, name in enumerate(NAMES):
        roster = ((300, 15), (340, 20), (310, 25), (365, 18))
        players = [skill(NAMES[i], *rating) for i, rating in enumerate(roster)]
        analysis = analysis_of(*roster, viewer=players[seat])
        for option in analysis.splits:
            assert name in option.side_a, (name, option)


def test_a_viewer_who_is_not_in_the_match_leaves_seat_order_alone_in_doubles():
    watcher = skill("edie", 300, 15)
    analysis = analysis_of((300, 15), (340, 20), (310, 25), (365, 18), viewer=watcher)
    for option in analysis.splits:
        assert option.side_a[0] == "ada"


def test_orientation_does_not_move_the_prediction_in_doubles():
    """Which side is yours is a rendering decision; how even the match is is not.

    The three arrangements come back in the same order, forecast identically,
    with only the two sides of each swapped — so a card cannot show two players
    of the same match two different balance percentages.
    """

    roster = ((300, 15), (340, 20), (310, 25), (365, 18))
    players = [skill(NAMES[i], *rating) for i, rating in enumerate(roster)]
    seen_by_ada = analysis_of(*roster, viewer=players[0])
    seen_by_bo = analysis_of(*roster, viewer=players[1])

    for mine, theirs in zip(seen_by_ada.splits, seen_by_bo.splits, strict=True):
        assert set(mine.side_a) == set(theirs.side_b) or set(mine.side_a) == set(
            theirs.side_a
        )
        assert mine.forecast.estimate == theirs.forecast.estimate
        assert mine.forecast.margin == theirs.forecast.margin
        assert mine.forecast.expected_gap == pytest.approx(theirs.forecast.expected_gap)


def test_a_split_carries_the_strengths_of_the_two_sides_it_names():
    """Membership and strength are built together, so the pair on ``side_a`` and
    the Level in ``forecast.side_a`` are the same team by construction."""

    roster = ((271, 0), (280, 0), (264, 0), (292, 0))
    players = [skill(NAMES[i], *rating) for i, rating in enumerate(roster)]
    by_name = {player.player: player for player in players}
    weight = CONSTANTS.weaker_partner_weight[Sport.PADEL]

    for option in analysis_of(*roster).splits:
        for names, strength in (
            (option.side_a, option.forecast.side_a),
            (option.side_b, option.forecast.side_b),
        ):
            first, second = (by_name[PlayerRef(name)] for name in names)
            assert side_of_two(first, second, weaker_weight=weight).strength == strength


# --- Team strength: not the average, and weighted the right way ----------------------


def test_a_team_strength_lies_between_its_two_partners_and_below_their_mean():
    """*Not the average*, and always on the weaker side of it — which is the
    whole claim the weighting makes and the only one that survives a retune."""

    weight = CONSTANTS.weaker_partner_weight[Sport.PADEL]
    for weaker_level, stronger_level in ((200, 450), (300, 305), (100, 500)):
        weaker = skill("weak", weaker_level, 20)
        stronger = skill("strong", stronger_level, 20)
        team = side_of_two(weaker, stronger, weaker_weight=weight)
        assert weaker.level <= team.strength <= stronger.level
        assert team.strength <= (weaker.level + stronger.level) / 2
        assert (team.strength == stronger.level) == (weaker.level == stronger.level)


def test_which_partner_is_the_weaker_one_does_not_depend_on_seat_order():
    weight = CONSTANTS.weaker_partner_weight[Sport.PADEL]
    ada, bo = skill("ada", 250, 40), skill("bo", 380, 10)
    assert side_of_two(ada, bo, weaker_weight=weight) == side_of_two(
        bo, ada, weaker_weight=weight
    )


def test_two_partners_at_exactly_the_same_level_break_the_tie_on_uncertainty():
    """Seat order is who pressed join first, and a forecast that turns on it is
    one where reseating the same four people changes the match.

    So an exact tie goes to the player the platform is least sure of — the
    assignment that gives the *wider* of the two available team σ, because when
    it cannot tell which of two equal players is weaker it does not get to pick
    the reading that flatters it. The strength is the same number either way,
    which is what makes this a choice about certainty alone.
    """

    weight = CONSTANTS.weaker_partner_weight[Sport.PADEL]
    settled, unsure = skill("settled", 300, 10), skill("unsure", 300, 120)
    team = side_of_two(settled, unsure, weaker_weight=weight)

    assert team == side_of_two(unsure, settled, weaker_weight=weight)
    assert team.strength == settled.level == unsure.level

    heavier, lighter = as_float(weight), 1 - as_float(weight)
    candidates = (
        combine_uncertainty(heavier * 1.20, lighter * 0.10),
        combine_uncertainty(heavier * 0.10, lighter * 1.20),
    )
    assert team.sigma == pytest.approx(max(candidates))
    assert max(candidates) > min(candidates)


def test_two_partners_identical_in_both_have_no_tie_left_to_break():
    weight = CONSTANTS.weaker_partner_weight[Sport.PADEL]
    twin, other = skill("twin", 300, 35), skill("other", 300, 35)
    assert side_of_two(twin, other, weaker_weight=weight) == side_of_two(
        other, twin, weaker_weight=weight
    )


def test_a_team_is_never_less_certain_than_its_most_uncertain_member():
    """Uncertainty propagates *through the weights*, which is averaging — so
    forming a team can only ever narrow it. Summed across the roster instead, it
    would grow with every player added, which is how a perfectly balanced padel
    match came to read 46%."""

    weight = CONSTANTS.weaker_partner_weight[Sport.PADEL]
    for first_sigma, second_sigma in ((0, 120), (84, 84), (35, 15), (0, 0)):
        team = side_of_two(
            skill("a", 300, first_sigma),
            skill("b", 340, second_sigma),
            weaker_weight=weight,
        )
        assert team.sigma <= max(first_sigma, second_sigma) / 100 + 1e-12
        assert team.sigma < (first_sigma + second_sigma) / 100 + 1e-12


def test_doubles_is_forecast_more_confidently_than_singles_between_the_same_people():
    """The consequence of propagating through the weights rather than across the
    roster, stated where a reader can check it: four freshly-onboarded players
    are a *narrower* claim than two, because a team strength is an average of two
    independent estimates."""

    four = doubles_forecast_of(*[(300, 84)] * 4)
    two = forecast_of(300, 300, 84, 84)
    assert four.margin < two.margin
    assert four.estimate > two.estimate


# --- The engine's own contract ----------------------------------------------------


def test_the_engine_satisfies_the_protocol():
    assert isinstance(ENGINE, BalanceForecastEngine)
    assert ENGINE.version == ENGINE_VERSION


def test_every_result_carries_the_version_that_produced_it():
    """A constant is falsifiable only against results it can be attributed to."""

    for snapshot in (
        singles(skill("a", 300, 20), skill("b", 340, 20)),
        doubles(*[skill(str(i), 300, 20) for i in range(4)]),
    ):
        analysis = ENGINE.analyse(snapshot=snapshot, now=NOW)
        assert analysis.engine_version == ENGINE_VERSION


def test_the_same_inputs_produce_the_same_analysis():
    """No clock, no randomness, no state between calls."""

    snapshot = singles(skill("a", 300, 35), skill("b", 341, 22))
    first = ENGINE.analyse(snapshot=snapshot, now=NOW)
    second = ENGINE.analyse(snapshot=snapshot, now=NOW)
    assert first == second


@pytest.mark.parametrize("field", ["second", "microsecond"])
def test_an_instant_that_is_not_rounded_to_the_minute_is_refused(field):
    """A caller's bug, not a domain state: a result carrying seconds is one no
    cache can ever hit and no replay can reproduce."""

    snapshot = singles(skill("a", 300, 20), skill("b", 300, 20))
    with pytest.raises(InvariantViolated, match="not rounded to the minute"):
        ENGINE.analyse(snapshot=snapshot, now=NOW.replace(**{field: 1}))


def test_the_forecast_does_not_depend_on_the_instant_it_is_asked_at():
    """It takes ``now`` and reads nothing from it — asserted, because a term that
    starts reading it later should have to say so."""

    snapshot = singles(skill("a", 300, 35), skill("b", 341, 22))
    later = NOW.replace(year=2031, month=1, day=2, hour=3, minute=4)
    assert (
        ENGINE.analyse(snapshot=snapshot, now=NOW).forecast
        == ENGINE.analyse(snapshot=snapshot, now=later).forecast
    )


@pytest.mark.parametrize("sport", [Sport.TENNIS, Sport.SQUASH])
def test_both_singles_sports_reach_the_same_arithmetic(sport):
    ada, bo = skill("ada", 300, 20), skill("bo", 350, 20)
    tennis = ENGINE.analyse(snapshot=singles(ada, bo, sport=Sport.TENNIS), now=NOW)
    other = ENGINE.analyse(snapshot=singles(ada, bo, sport=sport), now=NOW)
    assert tennis.forecast == other.forecast


def test_the_current_player_is_always_on_the_first_side():
    """A card drawing *you against them* from a result in seat order would draw
    it the wrong way round for half of all matches."""

    ada, bo = skill("ada", 320, 15), skill("bo", 280, 15)
    seated_first = forecast_of_snapshot(singles(ada, bo, viewer=ada))
    seated_second = forecast_of_snapshot(singles(ada, bo, viewer=bo))
    assert (seated_first.side_a, seated_first.side_b) == (ada.level, bo.level)
    assert (seated_second.side_a, seated_second.side_b) == (bo.level, ada.level)


def test_a_viewer_who_is_not_in_the_match_leaves_seat_order_alone():
    ada, bo = skill("ada", 320, 15), skill("bo", 280, 15)
    watcher = skill("cy", 300, 15)
    forecast = forecast_of_snapshot(singles(ada, bo, viewer=watcher))
    assert (forecast.side_a, forecast.side_b) == (ada.level, bo.level)


def test_orientation_does_not_move_the_prediction():
    """Sides are a rendering decision; the gap between them is symmetric."""

    ada, bo = skill("ada", 320, 15), skill("bo", 280, 40)
    one = forecast_of_snapshot(singles(ada, bo, viewer=ada))
    other = forecast_of_snapshot(singles(ada, bo, viewer=bo))
    assert (one.estimate, one.margin, one.certainty) == (
        other.estimate,
        other.margin,
        other.certainty,
    )


def forecast_of_snapshot(snapshot) -> BalanceForecast:
    result = ENGINE.analyse(snapshot=snapshot, now=NOW).forecast
    assert isinstance(result, Ok)
    return result.value


def test_every_value_object_in_the_vocabulary_is_frozen_and_closed():
    """``@final`` and ``frozen`` erase into nothing a behaviour test can see.

    The compiler *does* enforce both — ``tests/typecheck/kernel_misuse.py`` proves
    it, on a reason subclassed and a snapshot assigned to. What that harness
    cannot say is whether the decorator was applied to each class here, since a
    dropped one produces no error anywhere. So the list is written out: adding a
    value object means adding a line, which is the diff a reviewer should see.
    """

    vocabulary = (
        PlayerSkill,
        SeatSnapshot,
        MatchSnapshot,
        Side,
        SidesNotFormed,
        BalanceForecast,
        Split,
        PairingAnalysis,
        PairingConstants,
    )
    unclosed = [
        cls.__name__ for cls in vocabulary if not getattr(cls, "__final__", False)
    ]
    unfrozen = [
        cls.__name__ for cls in vocabulary if not cls.__dataclass_params__.frozen
    ]
    assert unclosed == [], unclosed
    assert unfrozen == [], unfrozen


# --- Gates over the source, for the claims a runtime test cannot make -------------


def _modules_of(package: Path) -> list[Path]:
    return sorted(package.rglob("*.py"))


def _parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_exactly_one_place_crosses_from_the_exact_vocabulary_into_floats():
    """*Where does this stop being exact* has one answer, and it is ``as_float``.

    A Level is a ``Ratio`` so that a doubles team strength is exact; a second
    ``float(...)`` somewhere else is a second place where that guarantee quietly
    ends, and it would end there for whoever reads that line only.
    """

    walked = _modules_of(PAIRING)
    crossings = [
        f"{path.relative_to(ROOT)}:{line} in {holder}"
        for path in walked
        for line, holder in _float_calls(_parsed(path))
    ]
    assert len(walked) >= 4, walked
    assert len(crossings) == 1, crossings
    assert crossings[0].endswith("in as_float"), crossings


def _float_calls(module: ast.Module) -> list[tuple[int, str]]:
    """Every ``float(...)`` in a module, with the function that holds it.

    Attributed by enclosing function rather than by line number: a pin on a line
    number goes red for a docstring edit, and a pin that goes red for the wrong
    reason is one somebody re-baselines without reading.
    """

    def calls(tree: ast.AST) -> list[int]:
        return [
            node.lineno
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "float"
        ]

    held = {
        line: node.name
        for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef)
        for line in calls(node)
    }
    return sorted((line, held.get(line, "<module>")) for line in calls(module))


def test_the_pairing_engine_does_not_import_the_rating_engine():
    """Same algebra, different question — and a lineage that must stay its own.

    ``racketskill/core`` combines uncertainties about *one player*; this combines
    two independent estimates into the gap between two sides. Importing it would
    put a balance percentage at the mercy of a rating-engine retune, and the
    falsification programme rests on attributing a number to one lineage.
    """

    walked = _modules_of(PAIRING) + [
        ROOT / "app" / "engines" / "forecast.py",
        ROOT / "app" / "engines" / "matchmaking.py",
    ]
    offenders = [
        f"{path.relative_to(ROOT)}:{node.lineno}: {name}"
        for path in walked
        for node in ast.walk(_parsed(path))
        for name in _imported_names(node)
        if name.startswith("app.engines.racketskill")
    ]
    assert len(walked) >= 6, walked
    assert not offenders, (
        "the pairing engine reached for the rating engine:\n" + "\n".join(offenders)
    )


def _imported_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and not node.level:
        return [node.module or ""]
    return []


def test_every_constant_carries_the_measurement_that_would_falsify_it():
    """A constant with no falsifying measurement is a preference wearing a
    number's clothes, and retuning it is taste rather than science."""

    source = _parsed(PAIRING / "v1" / "constants.py")
    declared = next(
        node
        for node in ast.walk(source)
        if isinstance(node, ast.ClassDef) and node.name == "PairingConstants"
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
    assert len([node for node in body if isinstance(node, ast.AnnAssign)]) == 5, (
        "the constant count moved — read the new one's falsifying note first"
    )
