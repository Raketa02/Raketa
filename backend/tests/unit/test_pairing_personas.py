"""The golden personas — **this file is meant to break on a constant retune.**

That is the point of it, and why it is kept apart from the invariants. Every
constant in the engine is an admitted hypothesis with a measurement that would
falsify it; when one is retuned these numbers *should* move, and updating them
should be a deliberate act with a reason rather than a red diff to make green.

Nothing here is an invariant. It is a snapshot of what the v1 constants produce
for six characteristic rosters, written as whole numbers a person can read.

Where these came from
---------------------
The source engine documents are not in this repository, and they publish no
worked singles forecast to reconcile against — what they publish is a canonical
*four-player padel* roster, which arrives with the three splits and is not this
slice's. So one persona is derived from a document that *is* here and the other
five are this engine's, under the constants as written:

* **The reference scenario** is not a baseline at all. ``gap_coefficient``'s own
  docstring commits the platform to *half a Level apart is 75% balanced*, and the
  coefficient is solved from that rather than chosen. This persona asserts the
  commitment end to end, so a retune that silently breaks the promise the constant
  was derived from cannot pass.
* **The onboarding pair** is pinned against ``racketskill/v3``'s σ floor rather
  than against a number typed here, because *"onboarding cannot produce confidence
  above 30%"* is the glossary's invariant and 0,84 is what it works out to. The
  mirrored assertion below is what keeps the two honest — the pairing engine
  deliberately does not import the rating engine, so a pair of assertions is the
  only mechanism available.
"""

import pytest

from app.engines.forecast import Certainty
from app.engines.pairing.v1 import CONSTANTS, PairingEngineV1
from app.engines.racketskill.core import CONFIDENCE_SIGMA_CEILING
from app.engines.racketskill.v3.engine import SIGMA_FLOOR
from app.kernel import Ok, Sport
from tests.unit.matchmaking_snapshots import NOW, singles, skill

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
