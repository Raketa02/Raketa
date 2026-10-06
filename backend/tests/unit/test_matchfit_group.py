"""A court's people read together: the forecast between two sides, the split it
was read from, and the hours everybody shares.

What the new games kept of the group objective (#580). The proposer ranks a
court's possible sides by the forecast, a Games card prints it, a booked game's
screen prints it with the two side strengths, and a card's overlap grade reads
the four-way availability — so these are the readings asserted here, against
the live ruleset's balance rules rather than numbers copied out of it.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from app.engines.matchfit.core import ForecastAssumption
from app.engines.matchfit.grouping import Forecast
from app.engines.matchfit.scorable import GridCell, LevelReading
from app.engines.matchfit.v1.group import (
    forecast,
    forecast_and_split,
    forecast_pct,
    group_availability,
)
from app.engines.racketskill.core import combine_sigma
from app.kernel import InvariantViolated, iso_weekday
from app.modules.matchmaking.domain.balance import combine_group_sigma
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET

#: The four-way spread, folded on RacketSkill's side of the fence exactly as the
#: module does it. Written through the composition seam and never as ``√(Σσ²)``:
#: a test with its own copy of an identity agrees with the engine until the day
#: the rule changes.
COMBINE = combine_group_sigma

RULES = LIVE_RULESET.balance


def cells(*specs: tuple[int, int]) -> tuple[GridCell, ...]:
    """``(weekday, the hour the cell starts at)`` pairs, as the engine reads them."""

    return tuple(GridCell(day=iso_weekday(day), hour=hour) for day, hour in specs)


def level(mu: float, sigma: float = 0.30) -> LevelReading:
    return LevelReading(mu=mu, sigma=sigma)


# ---------------------------------------------------------------------------
# Group availability
# ---------------------------------------------------------------------------


def test_group_availability_is_the_intersection_over_the_smallest_grid() -> None:
    """Among four people there is no *mine*, so the denominator is the least."""

    monday = cells((1, 19))
    two = cells((1, 19), (3, 19))
    three = cells((1, 19), (3, 19), (5, 19))

    assert group_availability((three, three, two, monday)) == pytest.approx(1.0)
    assert group_availability((three, three, three, two)) == pytest.approx(1.0)
    assert group_availability((three, two, two, cells((3, 19)))) == pytest.approx(1.0)
    assert group_availability((three, three)) == pytest.approx(1.0)
    assert group_availability((three, two)) == pytest.approx(1.0)
    assert group_availability((three, cells((1, 19), (2, 19)))) == pytest.approx(0.5)


def test_good_pairwise_overlaps_do_not_imply_a_shared_hour() -> None:
    """The failure a pair-by-pair reading cannot see, and why the court is read
    at once."""

    monday = cells((1, 19))
    tuesday = cells((2, 19))
    both = cells((1, 19), (2, 19))

    assert group_availability((both, monday, tuesday, monday)) == 0.0


def test_a_blank_grid_is_unknown_rather_than_no_overlap() -> None:
    """*Blank means we do not know* is not *you four never overlap*."""

    assert group_availability((cells((1, 19)), (), (), ())) is None
    assert group_availability((cells((1, 19)), cells((2, 19)))) == 0.0


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
def test_provisional_equals_full_the_moment_the_last_seat_fills(
    levels: tuple[float, float, float],
) -> None:
    """One implementation produces both figures, so the equality is a property.

    A half-empty side is read as if the missing player matched the one already
    there — implemented by seating that player twice — so filling the seat with
    the player the assumption named leaves the figure untouched and lifts only
    the caveat. That is the caveat being honest, asserted rather than hoped.
    """

    alone = level(levels[0], 0.30)
    other = (level(levels[1], 0.28), level(levels[2], 0.41))

    partial = forecast((alone,), other, RULES, COMBINE)
    filled = forecast((alone, alone), other, RULES, COMBINE)

    assert partial.pct == filled.pct
    assert partial.sigma_group == pytest.approx(filled.sigma_group)
    assert partial.provisional
    assert partial.assumption is ForecastAssumption.EMPTY_SEAT_MATCHES_ITS_PARTNER
    assert not filled.provisional


def test_a_side_with_nobody_on_it_is_not_a_side() -> None:
    """Refused rather than forecast, because there is nothing to assume about."""

    with pytest.raises(InvariantViolated, match="an empty side is not a side"):
        forecast((), (level(3.0),), RULES, COMBINE)


def test_a_side_over_its_seat_count_is_not_one_either() -> None:
    with pytest.raises(InvariantViolated, match="over its seat count"):
        forecast(
            (level(3.0), level(3.0)), (level(3.0),), RULES, COMBINE, seats_per_side=1
        )


def test_the_figure_is_the_clamped_line_over_the_side_gap() -> None:
    """``clamp(100 − gap·μ-coefficient − σ·σ-coefficient)``, over the two side
    strengths and the group σ — rounded once, to the printed whole percent."""

    ours = (level(3.20, 0.25), level(3.00, 0.30))
    theirs = (level(3.50, 0.40), level(2.80, 0.35))

    read, split = forecast_and_split(ours, theirs, RULES, COMBINE)

    sigma = COMBINE([0.25, 0.30, 0.40, 0.35])
    line = 100 - split.side_gap * RULES.mu_coefficient - sigma * RULES.sigma_coefficient
    assert read.sigma_group == pytest.approx(sigma)
    assert read.pct == round(min(RULES.pct_max, max(RULES.pct_min, line)))
    assert read.assumption is None


def test_the_clamp_bounds_the_figure_at_both_ends() -> None:
    assert forecast_pct(10.0, 0.0, RULES) == RULES.pct_min
    assert forecast_pct(0.0, 0.0, RULES) == RULES.pct_max


def test_the_group_sigma_is_combined_outside_the_engine() -> None:
    """Quadrature has one owner, and a fold of it is not a second rule."""

    sigmas = [0.30, 0.28, 0.41, 0.35]
    assert combine_group_sigma(sigmas) == pytest.approx(
        math.sqrt(2 * sum(sigma * sigma for sigma in sigmas) / len(sigmas))
    )


def test_two_players_combine_exactly_as_a_pair_does() -> None:
    """The basis, stated as an identity: at n = 2 this *is* ``combine_sigma``.

    Which is what makes it a re-basing rather than a retune — singles are
    untouched, so no released constant has moved under them.
    """

    assert combine_group_sigma([0.30, 0.41]) == pytest.approx(combine_sigma(0.30, 0.41))


def test_a_four_pays_what_the_pair_it_stands_for_pays() -> None:
    """The defect this exists to prevent, as arithmetic.

    ``√(Σσ²)`` grows with ``√n``, so four players at one σ handed the pairwise
    coefficient a number ``√2`` too large and were charged 1.41× for the identical
    per-player doubt. On the two-player basis a four of equals costs exactly what
    the pair of equals it stands for costs.
    """

    assert combine_group_sigma([0.35] * 4) == pytest.approx(combine_sigma(0.35, 0.35))
    # And the raw fold is the thing that was wrong: √2 larger, every time.
    assert math.sqrt(sum(0.35**2 for _ in range(4))) == pytest.approx(
        combine_group_sigma([0.35] * 4) * math.sqrt(2)
    )


def test_a_level_four_of_unsettled_players_is_no_longer_near_the_floor() -> None:
    """The symptom, pinned: gap 0,00 over 46 % was what the re-basing removed.

    The figure is still discounted for doubt — a separate question
    (``docs/handovers/the-forecast-percentage.md``) — but it is discounted once
    rather than 1.41 times, and the clamp no longer swallows it.
    """

    sigma = combine_group_sigma([0.846] * 4)
    pct = forecast_pct(0.0, sigma, RULES)

    assert pct == pytest.approx(61.7, abs=0.2)
    assert pct > RULES.pct_min


# ---------------------------------------------------------------------------
# The split
# ---------------------------------------------------------------------------


def test_the_split_is_the_two_strengths_the_forecast_was_read_from() -> None:
    """``pct`` says *how even*, and the split says *between what and what*.

    The failure this exists to prevent is a screen reading ``gap 0,00`` beside
    ``74% - fairly even``, which is what a client averaging levels for itself
    would print. **The weaker partner sets more of a side**, so a side's strength
    is the released share of its stronger player and the rest of its weaker.
    """

    share = RULES.stronger_partner_share
    ours = (level(3.00), level(3.80))
    theirs = (level(3.20), level(3.50))

    read, split = forecast_and_split(ours, theirs, RULES, COMBINE)

    assert split.your_side == pytest.approx(share * 3.80 + (1 - share) * 3.00)
    assert split.their_side == pytest.approx(share * 3.50 + (1 - share) * 3.20)
    assert split.gap == pytest.approx(split.your_side - split.their_side)
    assert split.side_gap == pytest.approx(abs(split.gap))
    assert read == forecast(ours, theirs, RULES, COMBINE)


def test_the_split_is_signed_and_the_first_side_is_yours() -> None:
    """``your_side`` is the first side handed over, always and by construction,
    so the orientation the client's bar takes is fixed here rather than
    negotiated — and swapping the sides only flips the sign."""

    strong = (level(4.00), level(4.00))
    weak = (level(2.00), level(2.00))

    _, ours_first = forecast_and_split(strong, weak, RULES, COMBINE)
    _, theirs_first = forecast_and_split(weak, strong, RULES, COMBINE)

    assert ours_first.your_side == pytest.approx(4.00)
    assert ours_first.their_side == pytest.approx(2.00)
    assert ours_first.gap == pytest.approx(2.00)
    assert theirs_first.gap == pytest.approx(-2.00)


def test_the_three_ways_to_split_a_four_are_three_different_games() -> None:
    """The share is what makes the proposer's choice between splits a choice:
    at parity every split of one four would forecast the same game."""

    a, b, c, d = level(3.00), level(3.20), level(3.50), level(3.80)
    gaps = sorted(
        round(forecast_and_split(ours, theirs, RULES, COMBINE)[1].gap, 3)
        for ours, theirs in (((a, b), (c, d)), ((a, c), (b, d)), ((a, d), (b, c)))
    )
    assert len(set(gaps)) == 3


def test_a_singles_split_is_two_players_and_their_difference() -> None:
    """One seat a side, so a side's strength is the player sitting in it, and
    nothing was assumed."""

    read, split = forecast_and_split(
        (level(3.40),), (level(3.00),), RULES, COMBINE, seats_per_side=1
    )
    assert split.your_side == pytest.approx(3.40)
    assert split.their_side == pytest.approx(3.00)
    assert split.gap == pytest.approx(0.40)
    assert read.provisional is False


def test_a_provisional_split_reads_the_empty_seat_the_way_pct_does() -> None:
    """All the numbers are carried under **one** assumption, or none of them.

    The empty seat is read as if the missing player matched the one already
    there, so seating that player's twin fills the seat without any number
    moving — and ``provisional`` goes on carrying the caveat for all of them.
    """

    ours = (level(3.00), level(2.80))
    lone = level(2.95)

    half_read, half = forecast_and_split(ours, (lone,), RULES, COMBINE)
    full_read, full = forecast_and_split(ours, (lone, lone), RULES, COMBINE)

    assert half_read.provisional is True
    assert full_read.provisional is False
    assert half == full
    assert half_read.pct == full_read.pct
