"""``window_of`` — the challenge window, **derived and never chosen**.

There is no window picker anywhere: a player changes their window by changing
their week, which is the same act that changes their matches. One control, one
meaning.

What is asserted is that every rung is a statement about the **week** rather than
about a pair, that the near rungs are relative to a weekday the caller supplies —
no date, no timezone — and that a blank week reads ``ANY``, because *any* is the
only rung that claims nothing.
"""

from __future__ import annotations

import pytest

from app.kernel import iso_weekday
from app.modules.player_profile.domain.weekly_hours import (
    HOURS_OF_THE_DAY,
    WINDOW_ANY_MIN_HOURS,
    WINDOW_SINGLE_DAY_MAX_HOURS,
    WeeklyHours,
    Window,
    window_of,
)

WEDNESDAY = iso_weekday(3)


def week(*codes: str) -> WeeklyHours:
    return WeeklyHours.from_codes(codes)


def test_a_blank_week_says_nothing_and_reads_any():
    """*We do not know* is not *never*, and ``ANY`` is the only rung that claims
    nothing about when."""

    assert window_of(WeeklyHours.blank(), WEDNESDAY) is Window.ANY


def test_a_wide_open_week_reads_any():
    codes = tuple(f"{day}:{at}" for day in range(1, 6) for at in HOURS_OF_THE_DAY)
    assert len(codes) >= WINDOW_ANY_MIN_HOURS
    assert window_of(week(*codes), WEDNESDAY) is Window.ANY


def test_one_short_of_wide_open_is_still_this_week():
    codes = tuple(f"{day}:{at}" for day in range(1, 6) for at in HOURS_OF_THE_DAY)
    assert window_of(week(*codes[: WINDOW_ANY_MIN_HOURS - 1]), WEDNESDAY) is (
        Window.THIS_WEEK
    )


def test_the_two_thresholds_keep_the_share_of_the_day_and_the_week_they_had():
    """The rescale ADR-0100 is amended by: *two parts of a day's three* and
    *twelve cells of the week's twenty-one*, read as the same share of sixteen
    hours and of a hundred and twelve, rounded down — so no threshold claims
    more of a week than it used to."""

    assert (WINDOW_SINGLE_DAY_MAX_HOURS, WINDOW_ANY_MIN_HOURS) == (10, 64)


def test_one_lightly_ticked_day_is_that_day():
    assert window_of(week("3:19", "3:20"), WEDNESDAY) is Window.TODAY
    assert window_of(week("4:19"), WEDNESDAY) is Window.TOMORROW
    assert window_of(week("6:10"), WEDNESDAY) is Window.THIS_WEEK


def test_tomorrow_wraps_the_week():
    """The week is an **ordinary** week and has no notion of a particular one, so
    Sunday's tomorrow is Monday."""

    assert window_of(week("1:19"), iso_weekday(7)) is Window.TOMORROW


def test_a_heavily_ticked_single_day_is_no_longer_a_window_on_that_day():
    """Past the cap it stops being *an evening* and starts being *a day*, which
    the near rungs do not claim to describe."""

    at_the_cap = tuple(
        f"3:{at}" for at in HOURS_OF_THE_DAY[:WINDOW_SINGLE_DAY_MAX_HOURS]
    )
    past_it = tuple(
        f"3:{at}" for at in HOURS_OF_THE_DAY[: WINDOW_SINGLE_DAY_MAX_HOURS + 1]
    )
    assert window_of(week(*at_the_cap), WEDNESDAY) is Window.TODAY
    assert window_of(week(*past_it), WEDNESDAY) is Window.THIS_WEEK


def test_saturday_and_sunday_alone_are_the_weekend():
    """A locale assumption, recorded as one rather than as a number to tune."""

    assert window_of(week("6:10", "7:19"), WEDNESDAY) is Window.WEEKEND


def test_a_weekend_plus_a_weekday_is_this_week():
    assert window_of(week("2:19", "6:10", "7:19"), WEDNESDAY) is Window.THIS_WEEK


@pytest.mark.parametrize("today", [iso_weekday(day) for day in range(1, 8)])
def test_the_window_is_always_one_of_the_five_codes(today):
    """A closed vocabulary, whatever day it is — *"tonight"* is the client's
    word, and there is no sixth code for it to arrive as."""

    assert window_of(week("2:19", "6:10"), today) in set(Window)
