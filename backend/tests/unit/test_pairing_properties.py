"""Bounds that must hold for *every* roster, not just the six personas.

The opposite file to the personas: nothing here should move when a constant is
retuned, because every assertion either reads the constant it is about or asserts
a shape. A retune that breaks one of these has broken the model.

The sweep is a seeded pseudo-random walk rather than a property-based library, so
it adds no dependency and a failure is reproducible from the seed printed in the
assertion — the argument ``test_racketskill_properties.py`` already makes.
"""

import random

import pytest

from app.engines.forecast import Certainty
from app.engines.pairing.core import (
    absolute_gap_deviation,
    as_float,
    combine_uncertainty,
    expected_absolute_gap,
)
from app.engines.pairing.v1 import CONSTANTS, PairingEngineV1
from app.kernel import Ok, Sport
from tests.unit.matchmaking_snapshots import NOW, singles, skill

ENGINE = PairingEngineV1()

#: The whole scale, in hundredths, plus the Uncertainties the platform actually
#: produces: certain, settled, calibrating, and the onboarding floor.
LEVELS = (100, 500)
SIGMAS = (0, 120)

ROSTERS = 400
SEED = 20260817

#: Grades in order of how much they claim. Compared by index, so the assertion is
#: *never claims more* rather than a string comparison that would silently pass.
CLAIMED = (Certainty.HIGH, Certainty.MODERATE, Certainty.LOW)


def forecast(level_a, level_b, sigma_a, sigma_b, sport=Sport.TENNIS):
    result = ENGINE.analyse(
        snapshot=singles(
            skill("a", level_a, sigma_a), skill("b", level_b, sigma_b), sport=sport
        ),
        now=NOW,
    ).forecast
    assert isinstance(result, Ok)
    return result.value


def rosters(seed=SEED, count=ROSTERS):
    draw = random.Random(seed)
    for _ in range(count):
        yield (
            draw.randint(*LEVELS),
            draw.randint(*LEVELS),
            draw.randint(*SIGMAS),
            draw.randint(*SIGMAS),
        )


# --- Outputs stay inside their ranges ---------------------------------------------


def test_every_output_stays_inside_its_range():
    for roster in rosters():
        result = forecast(*roster)
        assert CONSTANTS.balance_floor <= result.estimate <= 100, roster
        assert 50 <= result.favourite_share <= CONSTANTS.favourite_cap, roster
        assert 0 <= result.underdog_share <= 50, roster
        assert result.favourite_share + result.underdog_share == 100, roster
        assert result.margin >= 0, roster
        assert result.expected_gap >= 0.0, roster
        assert result.certainty in CLAIMED, roster


def test_the_identity_holds_for_every_roster():
    """The percentage and the bar, one number viewed twice, with no correction."""

    for roster in rosters():
        result = forecast(*roster)
        assert result.underdog_share == result.estimate // 2, roster


def test_the_reported_gap_is_never_below_the_gap_between_the_two_strengths():
    for roster in rosters():
        result = forecast(*roster)
        apart = abs(as_float(result.side_a) - as_float(result.side_b))
        assert result.expected_gap >= apart - 1e-9, roster


# --- Monotonicity: a wider gap never scores better --------------------------------


def test_a_level_further_from_the_opponent_never_raises_the_balance():
    """Closing the gap is the only thing that can make a match look more even."""

    draw = random.Random(SEED + 1)
    for _ in range(40):
        opponent = draw.randint(150, 450)
        sigma_a, sigma_b = draw.randint(*SIGMAS), draw.randint(*SIGMAS)
        walk = [
            forecast(min(500, opponent + apart), opponent, sigma_a, sigma_b)
            for apart in range(0, 260, 10)
        ]
        seed = (opponent, sigma_a, sigma_b)
        assert [f.estimate for f in walk] == sorted(
            (f.estimate for f in walk), reverse=True
        ), seed
        gaps = [f.expected_gap for f in walk]
        assert gaps == sorted(gaps), seed


# --- Monotonicity: knowing less never flatters ------------------------------------


def test_a_wider_uncertainty_never_raises_the_balance_or_the_certainty():
    """*Absence never flatters*, in the forecast's own terms.

    No match may look more even, or more confidently forecast, because the
    platform knows less about the two people in it. This is the same rule Match
    Fit's evidence terms carry, held here by the arithmetic rather than by a term
    kind.
    """

    draw = random.Random(SEED + 2)
    for _ in range(40):
        level_a, level_b = draw.randint(*LEVELS), draw.randint(*LEVELS)
        walk = [forecast(level_a, level_b, sigma, sigma) for sigma in range(0, 130, 5)]
        seed = (level_a, level_b)
        assert [f.estimate for f in walk] == sorted(
            (f.estimate for f in walk), reverse=True
        ), seed
        assert [f.margin for f in walk] == sorted(f.margin for f in walk), seed
        assert [CLAIMED.index(f.certainty) for f in walk] == sorted(
            CLAIMED.index(f.certainty) for f in walk
        ), seed


def test_a_wider_uncertainty_never_narrows_the_margin_around_any_gap():
    """The same claim one level down, on the arithmetic rather than the engine, so
    a retune of the coefficient cannot hide a break in the propagation."""

    for mean in (0.0, 0.05, 0.3, 0.9, 1.3, 2.5):
        widening = [absolute_gap_deviation(mean, spread) for spread in
                    (0.0, 0.05, 0.1, 0.2, 0.4, 0.6, 0.84, 1.2, 1.7)]
        assert widening == sorted(widening), mean
        assert widening[0] == 0.0


def test_combining_two_uncertainties_is_quadrature_and_not_a_sum():
    """Summed across a roster instead of propagated into the gap, σ comes out
    roughly twice too large — which is how a perfectly balanced match came to read
    46%. Pinned as arithmetic, because it is arithmetic."""

    assert combine_uncertainty(0.3, 0.4) == pytest.approx(0.5)
    assert combine_uncertainty(0.84, 0.84) == pytest.approx(1.18794, abs=5e-5)
    assert combine_uncertainty(0.84, 0.84) < 0.84 + 0.84


# --- The arithmetic underneath ------------------------------------------------------


def test_the_expected_absolute_gap_collapses_to_the_difference_when_certain():
    for mean in (-2.0, -0.5, 0.0, 0.25, 1.3, 4.0):
        assert expected_absolute_gap(mean, 0.0) == abs(mean)
        assert absolute_gap_deviation(mean, 0.0) == 0.0


def test_the_expected_absolute_gap_is_symmetric_in_the_direction_of_the_gap():
    """Which side is stronger changes who the favourite is, never how lopsided."""

    draw = random.Random(SEED + 3)
    for _ in range(60):
        mean = draw.uniform(0.0, 3.0)
        spread = draw.uniform(0.0, 1.5)
        assert expected_absolute_gap(mean, spread) == expected_absolute_gap(
            -mean, spread
        )


def test_the_forecast_is_symmetric_in_which_seat_holds_which_player():
    draw = random.Random(SEED + 4)
    for _ in range(60):
        level_a, level_b = draw.randint(*LEVELS), draw.randint(*LEVELS)
        sigma_a, sigma_b = draw.randint(*SIGMAS), draw.randint(*SIGMAS)
        one = forecast(level_a, level_b, sigma_a, sigma_b)
        other = forecast(level_b, level_a, sigma_b, sigma_a)
        seed = (level_a, level_b, sigma_a, sigma_b)
        assert (one.estimate, one.margin, one.certainty) == (
            other.estimate,
            other.margin,
            other.certainty,
        ), seed
        assert one.expected_gap == pytest.approx(other.expected_gap), seed
