"""``window_of`` — the challenge window, **derived and never chosen**.

There is no window picker anywhere: a player changes their window by changing
their grid, which is the same act that changes their matches. One control, one
meaning.

What is asserted is that every rung is a statement about the **grid** rather than
about a pair, that the near rungs are relative to a weekday the caller supplies —
no date, no timezone — and that a blank grid reads ``ANY``, because *any* is the
only rung that claims nothing.
"""

from __future__ import annotations

import pytest

from app.kernel import iso_weekday
from app.modules.player_profile.domain.availability import (
    WINDOW_ANY_MIN_SLOTS,
    WINDOW_SINGLE_DAY_MAX_SLOTS,
    AvailabilityGrid,
    DayPart,
    Window,
    window_of,
)

WEDNESDAY = iso_weekday(3)


def grid(*codes: str) -> AvailabilityGrid:
    return AvailabilityGrid.from_codes(codes)


def test_a_blank_grid_says_nothing_and_reads_any():
    """*We do not know* is not *never*, and ``ANY`` is the only rung that claims
    nothing about when."""

    assert window_of(AvailabilityGrid.blank(), WEDNESDAY) is Window.ANY


def test_a_wide_open_week_reads_any():
    codes = tuple(
        f"{day}:{part.value}" for day in range(1, 6) for part in DayPart
    )
    assert len(codes) >= WINDOW_ANY_MIN_SLOTS
    assert window_of(grid(*codes), WEDNESDAY) is Window.ANY


def test_one_lightly_ticked_day_is_that_day():
    assert window_of(grid("3:EVENING"), WEDNESDAY) is Window.TODAY
    assert window_of(grid("4:EVENING"), WEDNESDAY) is Window.TOMORROW
    assert window_of(grid("6:MORNING"), WEDNESDAY) is Window.THIS_WEEK


def test_tomorrow_wraps_the_week():
    """The grid is an **ordinary** week and has no notion of a particular one, so
    Sunday's tomorrow is Monday."""

    assert window_of(grid("1:EVENING"), iso_weekday(7)) is Window.TOMORROW


def test_a_heavily_ticked_single_day_is_no_longer_a_window_on_that_day():
    """Past the cap it stops being *an evening* and starts being *a day*, which
    the near rungs do not claim to describe."""

    codes = tuple(f"3:{part.value}" for part in DayPart)
    assert len(codes) > WINDOW_SINGLE_DAY_MAX_SLOTS
    assert window_of(grid(*codes), WEDNESDAY) is Window.THIS_WEEK


def test_saturday_and_sunday_alone_are_the_weekend():
    """A locale assumption, recorded as one rather than as a number to tune."""

    assert window_of(grid("6:MORNING", "7:EVENING"), WEDNESDAY) is Window.WEEKEND


def test_a_weekend_plus_a_weekday_is_this_week():
    assert (
        window_of(grid("2:EVENING", "6:MORNING", "7:EVENING"), WEDNESDAY)
        is Window.THIS_WEEK
    )


@pytest.mark.parametrize("today", [iso_weekday(day) for day in range(1, 8)])
def test_the_window_is_always_one_of_the_five_codes(today):
    """A closed vocabulary, whatever day it is — *"tonight"* is the client's
    word, and there is no sixth code for it to arrive as."""

    assert window_of(grid("2:EVENING", "6:MORNING"), today) in set(Window)
