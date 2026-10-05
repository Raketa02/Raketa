"""The overlap grid on a group-deck card, and its grade (#539; the mechanics
§8.1, the screens A2.3, Q71).

The card's people's week, summarised as **7 days × 3 ranges** — Morning 07–12,
Afternoon 12–17, Evening 17–23. A cell is **bright** where everybody on the card
is free for one whole hour in that range *together*, **dim** where all but one
are, and dark otherwise; the game's own cell is ringed. The grade is today's
engine reading of a group's overlap — the hours everybody shares over the week
of whoever has least to give — cut into *High*, *Good* and *Slim*.

The clock is Kraków's: Saturday 10 October 2026, 17:00 is a Saturday evening.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.kernel import Zone, instant
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.overlap import (
    DayRange,
    OverlapGrade,
    OverlapShade,
    overlap_of,
)

WARSAW = Zone("Europe/Warsaw")
SATURDAY_FIVE = instant(datetime(2026, 10, 10, 17, tzinfo=ZoneInfo("Europe/Warsaw")))
TUESDAY_HALF_SEVEN = instant(
    datetime(2026, 10, 6, 19, 30, tzinfo=ZoneInfo("Europe/Warsaw"))
)


def week(*cells: tuple[int, int]) -> WeeklyHours:
    return WeeklyHours.edited(cells)


def shade(overlap, day: int, range_: DayRange) -> OverlapShade:
    return next(
        cell.shade for cell in overlap.cells if cell.day == day and cell.range is range_
    )


def test_the_grid_is_seven_days_by_three_ranges_in_the_week_s_order():
    overlap = overlap_of([week((6, 17))], start=SATURDAY_FIVE, zone=WARSAW)

    assert [(cell.day, cell.range) for cell in overlap.cells] == [
        (day, range_)
        for day in range(1, 8)
        for range_ in (DayRange.MORNING, DayRange.AFTERNOON, DayRange.EVENING)
    ]


def test_bright_where_everybody_shares_one_hour_of_the_range():
    four = [
        week((6, 17), (2, 9)),
        week((6, 17), (2, 10)),
        week((6, 17)),
        week((6, 17), (2, 9)),
    ]

    overlap = overlap_of(four, start=SATURDAY_FIVE, zone=WARSAW)

    assert shade(overlap, 6, DayRange.EVENING) is OverlapShade.BRIGHT


def test_free_in_one_range_at_different_hours_is_not_together():
    # Everybody is free on Tuesday morning, but never at the same hour.
    four = [
        week((6, 17), (2, 7)),
        week((6, 17), (2, 8)),
        week((6, 17), (2, 9)),
        week((6, 17), (2, 10)),
    ]

    overlap = overlap_of(four, start=SATURDAY_FIVE, zone=WARSAW)

    assert shade(overlap, 2, DayRange.MORNING) is OverlapShade.DARK


def test_dim_where_all_but_one_are_free_together():
    four = [
        week((6, 17), (3, 13)),
        week((6, 17), (3, 13)),
        week((6, 17), (3, 13)),
        week((6, 17)),
    ]

    overlap = overlap_of(four, start=SATURDAY_FIVE, zone=WARSAW)

    assert shade(overlap, 3, DayRange.AFTERNOON) is OverlapShade.DIM


def test_dark_where_two_of_four_are_missing():
    four = [
        week((6, 17), (3, 13)),
        week((6, 17), (3, 13)),
        week((6, 17)),
        week((6, 17)),
    ]

    overlap = overlap_of(four, start=SATURDAY_FIVE, zone=WARSAW)

    assert shade(overlap, 3, DayRange.AFTERNOON) is OverlapShade.DARK


def test_two_people_have_no_dim_cell_because_all_but_one_is_one_person():
    two = [week((6, 17), (1, 8)), week((6, 17))]

    overlap = overlap_of(two, start=SATURDAY_FIVE, zone=WARSAW)

    assert shade(overlap, 1, DayRange.MORNING) is OverlapShade.DARK
    assert {cell.shade for cell in overlap.cells} == {
        OverlapShade.BRIGHT,
        OverlapShade.DARK,
    }


def test_the_game_s_cell_is_its_local_day_and_the_range_its_hour_starts_in():
    overlap = overlap_of(
        [week((2, 19), (2, 20))], start=TUESDAY_HALF_SEVEN, zone=WARSAW
    )

    assert (overlap.game.day, overlap.game.range) == (2, DayRange.EVENING)


def test_everybody_sharing_most_of_the_narrowest_week_is_high():
    evenings = [(day, hour) for day in (2, 4) for hour in (18, 19, 20)]
    four = [
        week(*evenings, (6, 17)),
        week(*evenings, (6, 17), (1, 8), (1, 9)),
        week(*evenings, (6, 17), (5, 12)),
        week(*evenings, (6, 17)),
    ]

    overlap = overlap_of(four, start=SATURDAY_FIVE, zone=WARSAW)

    assert overlap.grade is OverlapGrade.HIGH


def test_a_quarter_to_a_half_of_the_narrowest_week_is_good():
    # Seven hours shared, the narrowest week holding twenty.
    shared = [(6, 17), (2, 18), (2, 19), (4, 18), (4, 19), (5, 20), (7, 10)]
    own = [(1, hour) for hour in range(7, 20)]
    two = [week(*shared, *own), week(*shared, *[(3, hour) for hour in range(7, 22)])]

    overlap = overlap_of(two, start=SATURDAY_FIVE, zone=WARSAW)

    assert overlap.grade is OverlapGrade.GOOD


def test_only_the_game_s_hour_in_common_is_slim():
    two = [
        week((6, 17), *[(1, hour) for hour in range(7, 20)]),
        week((6, 17), *[(3, hour) for hour in range(7, 20)]),
    ]

    overlap = overlap_of(two, start=SATURDAY_FIVE, zone=WARSAW)

    assert overlap.grade is OverlapGrade.SLIM


def test_a_blank_week_on_the_card_is_slim_and_never_bright():
    overlap = overlap_of(
        [week((6, 17)), WeeklyHours.blank()], start=SATURDAY_FIVE, zone=WARSAW
    )

    assert overlap.grade is OverlapGrade.SLIM
    assert shade(overlap, 6, DayRange.EVENING) is OverlapShade.DARK
