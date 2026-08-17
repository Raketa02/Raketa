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
    side_of_two,
)
from app.engines.pairing.v1 import CONSTANTS, PairingEngineV1
from app.kernel import Ok, Sport
from tests.unit.matchmaking_snapshots import NOW, doubles, singles, skill

ENGINE = PairingEngineV1()

#: Seat names, so that a failing roster prints as four people rather than four
#: indices.
NAMES = ("ada", "bo", "cy", "dee")

#: The weight the doubles path runs under. Read from the constants rather than
#: typed, because nothing in this file may move when it is retuned.
WEIGHT = CONSTANTS.weaker_partner_weight[Sport.PADEL]

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


def players_of(*roster):
    """Four players from four (Level, σ) pairs. The name travels with the rating,
    which is what makes reseating them a permutation of *people* rather than a
    relabelling."""

    return [skill(NAMES[seat], *rating) for seat, rating in enumerate(roster)]


def seated(*players, sport=Sport.PADEL):
    return ENGINE.analyse(snapshot=doubles(*players, sport=sport), now=NOW)


def four(*roster, sport=Sport.PADEL):
    """The whole analysis of one four-player roster, given as (Level, σ) pairs."""

    return seated(*players_of(*roster), sport=sport)


def foursomes(seed=SEED + 10, count=ROSTERS):
    """Four-player rosters, a quarter of them drawn off a coarse grid.

    The coarse ones are the point: a Level drawn from the whole scale ties with
    another about once in four hundred, so a sweep over open draws alone would
    almost never form a team of two players at exactly the same Level — the one
    case where *which partner is the weaker one* has no answer and a rule has to
    supply one. A grid of nine makes the tie ordinary instead of a coincidence.
    """

    draw = random.Random(seed)
    grid = tuple(range(100, 501, 50))
    for index in range(count):
        levels = grid if index % 4 == 0 else None
        yield tuple(
            (
                draw.choice(levels) if levels else draw.randint(*LEVELS),
                draw.randint(*SIGMAS),
            )
            for _ in range(4)
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
        widening = [
            absolute_gap_deviation(mean, spread)
            for spread in (0.0, 0.05, 0.1, 0.2, 0.4, 0.6, 0.84, 1.2, 1.7)
        ]
        assert widening == sorted(widening), mean
        assert widening[0] == 0.0


def test_combining_two_uncertainties_is_quadrature_and_not_a_sum():
    """Summed across a roster instead of propagated into the gap, σ comes out
    roughly twice too large — which is how a perfectly balanced match came to read
    46%. Pinned as arithmetic, because it is arithmetic."""

    assert combine_uncertainty(0.3, 0.4) == pytest.approx(0.5)
    assert combine_uncertainty(0.84, 0.84) == pytest.approx(1.18794, abs=5e-5)
    assert combine_uncertainty(0.84, 0.84) < 0.84 + 0.84


# --- Doubles: the same bounds, plus the ones the pairing decision adds ---------------


def test_every_doubles_output_stays_inside_its_range():
    """The singles bounds, unchanged, on the path that adds a pairing decision
    and a weighted team strength in front of them."""

    for roster in foursomes():
        analysis = four(*roster)
        assert isinstance(analysis.forecast, Ok), roster
        assert len(analysis.splits) == 3, roster
        for option in analysis.splits:
            result = option.forecast
            assert CONSTANTS.balance_floor <= result.estimate <= 100, roster
            assert 50 <= result.favourite_share <= CONSTANTS.favourite_cap, roster
            assert result.underdog_share == result.estimate // 2, roster
            assert result.favourite_share + result.underdog_share == 100, roster
            assert result.margin >= 0, roster
            assert result.expected_gap >= 0.0, roster
            assert result.certainty in CLAIMED, roster


def test_the_winner_is_the_arrangement_with_the_smallest_expected_gap():
    """Ranked, and the ranking is the selection. There is no separate choice of
    winner that could disagree with the order the three are returned in."""

    for roster in foursomes():
        analysis = four(*roster)
        gaps = [option.forecast.expected_gap for option in analysis.splits]
        assert gaps[0] == min(gaps), roster
        assert gaps == sorted(gaps), roster
        assert analysis.forecast.value is analysis.splits[0].forecast, roster


def test_every_player_is_seated_exactly_once_in_every_arrangement():
    for roster in foursomes():
        for option in four(*roster).splits:
            assert sorted(option.side_a + option.side_b) == sorted(NAMES), roster


def test_which_seat_a_player_sits_in_does_not_change_the_match():
    """The three splits are a property of the four *people*, not of the order
    they joined in. A roster dealt into different seats must produce the same
    three arrangements with the same forecasts — otherwise the engine's answer
    depends on who pressed join first."""

    draw = random.Random(SEED + 11)
    for roster in foursomes(count=80):
        players = players_of(*roster)
        order = list(range(4))
        draw.shuffle(order)
        reseated = [players[seat] for seat in order]

        def arrangements(analysis):
            return {
                frozenset({frozenset(o.side_a), frozenset(o.side_b)}): o.forecast
                for o in analysis.splits
            }

        as_joined = arrangements(seated(*players))
        redealt = arrangements(seated(*reseated))
        assert as_joined.keys() == redealt.keys(), (roster, order)
        for arrangement, forecast in as_joined.items():
            other = redealt[arrangement]
            assert forecast.estimate == other.estimate, (roster, order)
            assert forecast.margin == other.margin, (roster, order)
            assert forecast.expected_gap == pytest.approx(other.expected_gap)


def test_a_wider_uncertainty_never_raises_the_doubles_balance_or_certainty():
    """*Absence never flatters*, on the arity where it would be easiest to hide:
    a team strength averages two estimates, so it narrows — but it never narrows
    below what the platform actually knows."""

    draw = random.Random(SEED + 12)
    for _ in range(30):
        levels = [draw.randint(*LEVELS) for _ in range(4)]
        walk = [
            four(*[(level, sigma) for level in levels]).splits[0].forecast
            for sigma in range(0, 130, 10)
        ]
        assert [f.estimate for f in walk] == sorted(
            (f.estimate for f in walk), reverse=True
        ), levels
        assert [f.margin for f in walk] == sorted(f.margin for f in walk), levels
        assert [CLAIMED.index(f.certainty) for f in walk] == sorted(
            CLAIMED.index(f.certainty) for f in walk
        ), levels


def test_a_stronger_partner_never_weakens_a_team():
    """Monotone in both partners' Levels, which is what stops a team strength
    being a place a rating improvement could quietly cost a player."""

    draw = random.Random(SEED + 13)
    for _ in range(60):
        partner = skill("partner", draw.randint(*LEVELS), draw.randint(*SIGMAS))
        sigma = draw.randint(*SIGMAS)
        walk = [
            side_of_two(
                skill("mover", level, sigma), partner, weaker_weight=WEIGHT
            ).strength
            for level in range(100, 501, 20)
        ]
        assert walk == sorted(walk), (partner, sigma)


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
