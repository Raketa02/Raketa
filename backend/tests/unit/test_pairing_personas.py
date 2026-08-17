"""The golden personas — **this file is meant to break on a constant retune.**

That is the point of it, and why it is kept apart from the invariants. Every
constant in the engine is an admitted hypothesis with a measurement that would
falsify it; when one is retuned these numbers *should* move, and updating them
should be a deliberate act with a reason rather than a red diff to make green.

Nothing here is an invariant. It is a snapshot of what the v1 constants produce
for six characteristic rosters, written as whole numbers a person can read.

Where these came from
---------------------
The source engine documents are not in this repository. Two personas are
therefore derived from documents that *are* here, and the rest are this engine's
own, under the constants as written:

* **The reference scenario** is not a baseline at all. ``gap_coefficient``'s own
  docstring commits the platform to *half a Level apart is 75% balanced*, and the
  coefficient is solved from that rather than chosen. This persona asserts the
  commitment end to end, so a retune that silently breaks the promise the constant
  was derived from cannot pass.
* **The canonical padel roster** is the same shape one arity up.
  [ADR-0025](../../../docs/adr/0025-binding-pairing-for-counted-matches.md)
  records four Levels and two of the three gaps they split into, and those two
  figures are the pair of linear equations ``weaker_partner_weight`` was solved
  from. So this persona is not a screenshot; it is the derivation, asserted
  through the engine.
* **The onboarding pair** is pinned against ``racketskill/v3``'s σ floor rather
  than against a number typed here, because *"onboarding cannot produce confidence
  above 30%"* is the glossary's invariant and 0,84 is what it works out to. The
  mirrored assertion below is what keeps the two honest — the pairing engine
  deliberately does not import the rating engine, so a pair of assertions is the
  only mechanism available.
"""

import pytest

from app.engines.forecast import Certainty
from app.engines.pairing.core import as_float
from app.engines.pairing.v1 import CONSTANTS, PairingEngineV1
from app.engines.racketskill.core import CONFIDENCE_SIGMA_CEILING
from app.engines.racketskill.v3.engine import SIGMA_FLOOR
from app.kernel import Ok, Sport
from tests.unit.matchmaking_snapshots import NOW, doubles, singles, skill

ENGINE = PairingEngineV1()

#: σ at the onboarding ceiling, in the hundredths the snapshot carries. Written
#: here and asserted against the rating engine below rather than imported into the
#: engine, which must not restate the confidence transform or its ceiling.
ONBOARDING_SIGMA = 84


def forecast(first, second, *, sport=Sport.TENNIS, viewer=None):
    result = ENGINE.analyse(
        snapshot=singles(first, second, sport=sport, viewer=viewer), now=NOW
    ).forecast
    assert isinstance(result, Ok)
    return result.value


def pairing(*players, sport=Sport.PADEL, viewer=None):
    """The whole analysis of a four-player match: the ranked splits and the
    winner's forecast, which is the one a card shows."""

    return ENGINE.analyse(
        snapshot=doubles(*players, sport=sport, viewer=viewer), now=NOW
    )


def paper_gap(option):
    """The distance between the two team strengths, exactly. Levels are exact
    ratios all the way through the weighted blend, so this is the figure a
    document can state to four decimals and a test can assert to the hundredth of
    a hundredth."""

    return abs(as_float(option.forecast.side_a) - as_float(option.forecast.side_b))


def test_the_reference_scenario_the_coefficient_was_solved_from():
    """*A singles match between 3,00 and 3,50 is 75% balanced, a 63/37 split.*

    This is the product commitment ``gap_coefficient`` is derived from, asserted
    through the engine rather than against the constant. Retuning the coefficient
    means revising this sentence — which is the difference between science and
    nudging a number until a screenshot looks right.
    """

    result = forecast(skill("ada", 300, 0), skill("bo", 350, 0))
    assert result.estimate == 75
    assert (result.favourite_share, result.underdog_share) == (63, 37)
    assert result.margin == 0
    assert result.certainty is Certainty.HIGH
    assert result.beyond_scale is False


def test_two_players_the_platform_knows_exactly_and_who_are_dead_level():
    """The top of the scale, and the only forecast that is 50/50."""

    result = forecast(skill("ada", 320, 0), skill("bo", 320, 0))
    assert result.estimate == 100
    assert (result.favourite_share, result.underdog_share) == (50, 50)
    assert result.margin == 0
    assert result.expected_gap == 0.0
    assert result.fit_to_print is True


def test_two_freshly_onboarded_players_are_suppressed_rather_than_confident():
    """The persona the whole margin exists for.

    Both players answered a questionnaire and nothing else, so σ sits at the
    onboarding floor for both. Their Levels are twelve hundredths apart — as close
    as any two ratings get — and the honest forecast is not *96% balanced*. It is
    *we expect about a Level of daylight and we do not know which way*: a point
    estimate near the middle of the scale with a margin wider than a third of it,
    graded LOW, and a card that declines to print it.

    The estimate is still returned, because it still ranks. Suppression is
    presentation.
    """

    result = forecast(
        skill("ada", 300, ONBOARDING_SIGMA), skill("bo", 312, ONBOARDING_SIGMA)
    )
    assert result.estimate == 52
    assert result.margin == 36
    assert result.certainty is Certainty.LOW
    assert result.fit_to_print is False
    assert result.expected_gap == pytest.approx(0.9527, abs=5e-5)
    assert result.beyond_scale is False


def test_the_onboarding_sigma_here_is_still_the_one_the_rating_engine_enforces():
    """The mirrored half of the persona above.

    ``ONBOARDING_SIGMA`` is a number typed into a test for an engine that must not
    import the rating engine. If the questionnaire's confidence ceiling moves, the
    persona above stops describing a freshly-onboarded player and starts
    describing nobody — quietly, and while staying green. This is what makes that
    loud. Same mechanism, and the same argument, as ``test_band_edges_mirrored``.
    """

    assert SIGMA_FLOOR == pytest.approx(ONBOARDING_SIGMA / 100)
    assert round(100 * (1 - SIGMA_FLOOR / CONFIDENCE_SIGMA_CEILING)) == 30


def test_a_settled_pair_at_a_club_prints_with_a_moderate_margin():
    """The ordinary case a home screen is mostly made of: two players with a
    season of counted matches behind them, a quarter of a Level apart."""

    result = forecast(skill("ada", 320, 20), skill("bo", 345, 25))
    assert result.estimate == 84
    assert (result.favourite_share, result.underdog_share) == (58, 42)
    assert result.margin == 12
    assert result.certainty is Certainty.MODERATE
    assert result.fit_to_print is True


def test_a_mismatch_reports_the_floor_and_says_the_scale_ran_out():
    """2,50 against 4,20 is not a close match with a number attached.

    The percentage saturates at the floor and the bar at its cap, together — and
    ``beyond_scale`` is what a card reads to say *mismatch* rather than *35%*. The
    gap the caller is handed is the real 1,70, so two mismatches remain rankable
    against each other.
    """

    result = forecast(skill("ada", 250, 15), skill("bo", 420, 15))
    assert result.estimate == CONSTANTS.balance_floor == 35
    assert (result.favourite_share, result.underdog_share) == (83, 17)
    assert result.favourite_share == CONSTANTS.favourite_cap
    assert result.beyond_scale is True
    assert result.expected_gap == pytest.approx(1.70)
    assert result.certainty is Certainty.MODERATE


# --- Doubles: the three splits ------------------------------------------------------


def test_the_canonical_padel_roster_the_weighting_was_solved_from():
    """*2,71 / 2,80 / 2,64 / 2,92 split one way give a gap of 0,0155 between team
    strengths and split another give 0,1825 — an order of magnitude apart, from
    the same four people.*

    ADR-0025's opening paragraph, asserted through the engine. Those two figures
    are each one linear equation in ``weaker_partner_weight`` and both are solved
    by 0,55; a retune moves them, which is the point of this file. The platform's
    Uncertainty is set aside here — every player exact — so that the expected gap
    collapses to the paper gap and the numbers on the page are the numbers the
    document wrote down.

    It is also the argument for choosing the split at all rather than letting
    four adults sort it out: the same four people are a 99%-balanced match or a
    91% one depending only on how they are arranged.
    """

    analysis = pairing(
        skill("ada", 271, 0),
        skill("bo", 280, 0),
        skill("cy", 264, 0),
        skill("dee", 292, 0),
    )
    best, middle, worst = analysis.splits

    assert (best.side_a, best.side_b) == (("ada", "bo"), ("cy", "dee"))
    assert paper_gap(best) == pytest.approx(0.0155)
    assert (worst.side_a, worst.side_b) == (("ada", "cy"), ("bo", "dee"))
    assert paper_gap(worst) == pytest.approx(0.1825)
    assert (middle.side_a, middle.side_b) == (("ada", "dee"), ("bo", "cy"))
    assert paper_gap(middle) == pytest.approx(0.0925)

    assert [option.forecast.estimate for option in analysis.splits] == [99, 95, 91]
    assert isinstance(analysis.forecast, Ok)
    assert analysis.forecast.value is best.forecast
    assert best.forecast.certainty is Certainty.HIGH
    assert (best.forecast.favourite_share, best.forecast.underdog_share) == (51, 49)


def test_the_same_roster_as_the_platform_actually_knows_it():
    """The card a settled club four would really see, with the persona above's
    Uncertainties put back.

    Nobody is exact, so the estimate falls — 92 rather than 99 — and the margin
    stops being zero, while the arrangement chosen and the order of the three do
    not move. That separation is the design: Uncertainty reaches the percentage
    only by widening the gap, and it reaches the *choice* only by making a split
    the platform is unsure about less attractive than one it is sure of.
    """

    analysis = pairing(
        skill("ada", 271, 15),
        skill("bo", 280, 20),
        skill("cy", 264, 25),
        skill("dee", 292, 18),
    )
    best = analysis.splits[0]

    assert (best.side_a, best.side_b) == (("ada", "bo"), ("cy", "dee"))
    assert best.forecast.estimate == 92
    assert best.forecast.margin == 6
    assert best.forecast.certainty is Certainty.HIGH
    assert (best.forecast.favourite_share, best.forecast.underdog_share) == (54, 46)
    assert [option.forecast.estimate for option in analysis.splits] == [92, 91, 89]


def test_four_freshly_onboarded_players_degrade_rather_than_look_perfect():
    """The persona the whole treatment of Uncertainty exists for, in doubles.

    Four people who have answered a questionnaire and played nothing. Their paper
    Levels are within a third of a Level of each other and the best arrangement's
    two team strengths are three hundredths apart — on paper a near-perfect
    match, and a naive engine would quote it at 99% and mean nothing by it.

    What comes back instead is 66% with a margin of 25 points, graded LOW and not
    fit to print: *we expect the better part of a Level of daylight and we do not
    know which way.* The estimate is still returned, because it still ranks, and
    the ranking between the three arrangements is still made — the platform
    simply declines to print a number it cannot stand behind.
    """

    analysis = pairing(
        skill("ada", 300, ONBOARDING_SIGMA),
        skill("bo", 312, ONBOARDING_SIGMA),
        skill("cy", 295, ONBOARDING_SIGMA),
        skill("dee", 325, ONBOARDING_SIGMA),
    )
    best = analysis.splits[0]

    assert (best.side_a, best.side_b) == (("ada", "bo"), ("cy", "dee"))
    assert paper_gap(best) == pytest.approx(0.031)
    assert best.forecast.estimate == 66
    assert best.forecast.margin == 25
    assert best.forecast.certainty is Certainty.LOW
    assert best.forecast.fit_to_print is False
    assert best.forecast.beyond_scale is False
    assert [option.forecast.estimate for option in analysis.splits] == [66, 66, 65]


def test_a_badminton_four_reaches_the_same_arithmetic_as_a_padel_four():
    """Both sports carry the same weight at v1, so the two answers are identical
    today. They are computed through separate constants, which is what makes
    *does a badminton partnership forgive differently?* a measurement."""

    roster = (
        skill("ada", 271, 15),
        skill("bo", 280, 20),
        skill("cy", 264, 25),
        skill("dee", 292, 18),
    )
    padel = pairing(*roster, sport=Sport.PADEL)
    badminton = pairing(*roster, sport=Sport.BADMINTON)
    assert padel.splits == badminton.splits


# --- What a forming match says about the seats it has not filled --------------------


def seat_target(*occupants, sport=Sport.PADEL):
    result = ENGINE.analyse(
        snapshot=doubles(*occupants, sport=sport), now=NOW
    ).seat_target
    assert isinstance(result, Ok), result
    return as_float(result.value)


def test_the_canonical_padel_roster_one_seat_short_says_what_it_is_aiming_at():
    """ADR-0025's four, with the 2,92 not yet arrived.

    The three seated Levels admit three Levels that would even the match — 2,42
    partnered with the 2,80, **2,71 partnered with the 2,71**, and 3,52 partnered
    with the 2,64 — and the middle one is what the card advertises. So the seat
    reads *aimed at 2,71*, which is a Level a player can hold themselves up
    against, and it is inside the three Levels already there rather than at either
    extreme.

    Read against the persona above, this is also what the seat target is *for*:
    the player who actually took that seat was a 2,92, three tenths above what it
    was aimed at, and that is exactly why the real match comes back 99% balanced
    rather than exactly even.
    """

    ada, bo, cy = skill("ada", 271, 15), skill("bo", 280, 20), skill("cy", 264, 25)
    assert seat_target(ada, bo, cy, None) == pytest.approx(2.7144, abs=5e-5)

    analysis = ENGINE.analyse(snapshot=doubles(ada, bo, cy, None), now=NOW)
    assert isinstance(analysis.target_band, Ok)
    band = analysis.target_band.value
    assert as_float(band.midpoint) == pytest.approx(2.7167, abs=5e-5)
    assert (as_float(band.low), as_float(band.high)) == pytest.approx(
        (2.2167, 3.2167), abs=5e-5
    )


def test_the_seat_target_a_scan_of_the_scale_would_have_got_wrong():
    """A 2,00, a 3,00 and a 4,00, with one seat left.

    Three Levels even this match: **1,18** beside the 4,00, **2,82** beside the
    3,00, and **5,22** beside the 2,00 — every one of them a dead-level match on
    paper, so *as even as possible* does not choose between them and something
    has to. A scan walking the scale upwards keeps the first of the tying
    candidates it meets and answers 1,18, which advertises a match of 2/3/4 to a
    near-beginner. The middle answer is 2,82, and it is the only one of the three
    that a player looking at those three Levels would recognise as being about
    them.
    """

    roster = (skill("ada", 200, 0), skill("bo", 300, 0), skill("cy", 400, 0))
    assert seat_target(*roster, None) == pytest.approx(2.8182, abs=5e-5)


def test_a_singles_match_with_a_seat_open_aims_at_the_seated_players_own_level():
    """No pairing, so no arrangement to choose and nothing to solve: the ideal
    opponent for a 3,17 is a 3,17."""

    ada = skill("ada", 317, 20)
    result = ENGINE.analyse(snapshot=singles(ada, None), now=NOW).seat_target
    assert isinstance(result, Ok)
    assert as_float(result.value) == pytest.approx(3.17)


def test_a_match_with_two_seats_open_advertises_a_band_instead():
    """The question is under-determined with two Levels to choose and one
    equation between them, so the precise answer is refused and the blunt one is
    given: two players averaging 3,05 are looking for a 2,55 to 3,55."""

    analysis = ENGINE.analyse(
        snapshot=doubles(skill("ada", 290, 20), skill("bo", 320, 20), None, None),
        now=NOW,
    )
    assert analysis.seat_target.reason.kind == "seat_under_determined"
    assert analysis.seat_target.reason.open_seats == 2

    assert isinstance(analysis.target_band, Ok)
    band = analysis.target_band.value
    assert as_float(band.midpoint) == pytest.approx(3.05)
    assert (as_float(band.low), as_float(band.high)) == pytest.approx((2.55, 3.55))


def test_the_band_is_as_wide_as_the_platform_said_a_match_could_be():
    """The band's half width is not a second opinion about how far apart two
    players can be. It is the reference scenario ``gap_coefficient`` was solved
    from, pointed the other way: half a Level apart is 75% balanced, and 75% is
    the edge of what the platform has said out loud is still a match. So the two
    constants are checked against each other here, and a retune of either that
    leaves them disagreeing turns this red.
    """

    half_width = CONSTANTS.target_band_half_width
    assert 100 - CONSTANTS.gap_coefficient * half_width == 75

    edge = ENGINE.analyse(
        snapshot=singles(skill("ada", 300, 0), skill("bo", 350, 0)), now=NOW
    ).forecast
    assert isinstance(edge, Ok)
    assert as_float(half_width) == pytest.approx(0.50)
    assert edge.value.estimate == 75


def test_a_squash_match_seen_by_the_player_on_the_second_seat():
    """Same arithmetic, sides the other way up.

    Bo is looking at a match Ada created, so Bo is side A. The prediction does not
    move — the gap between two sides is symmetric — and only the two strengths
    swap, which is what a card needs to draw *you against them* the right way
    round.
    """

    ada, bo = skill("ada", 290, 30), skill("bo", 325, 25)
    seen_by_bo = forecast(ada, bo, sport=Sport.SQUASH, viewer=bo)
    assert seen_by_bo.estimate == 79
    assert (seen_by_bo.favourite_share, seen_by_bo.underdog_share) == (61, 39)
    assert seen_by_bo.margin == 15
    assert seen_by_bo.certainty is Certainty.MODERATE
    assert (seen_by_bo.side_a, seen_by_bo.side_b) == (bo.level, ada.level)

    seen_by_ada = forecast(ada, bo, sport=Sport.SQUASH, viewer=ada)
    assert (seen_by_ada.side_a, seen_by_ada.side_b) == (ada.level, bo.level)
    assert seen_by_ada.estimate == seen_by_bo.estimate
