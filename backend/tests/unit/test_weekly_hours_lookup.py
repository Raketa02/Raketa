"""*Is this hour ticked?* is answered by lookup, not by scanning (#703,
ADR-0197 §2b).

The overlap grid asks it for 21 cells × every hour in each cell's range × each
person on a card × every dealt card, and *free for the hour* asks it for the
proposer, Post a game's grid and rescues. The answer must be the one the scan
gave, for every hour of the week, and the week must stay the same value.
"""

from __future__ import annotations

import pickle
from dataclasses import replace

import pytest

from app.kernel import iso_weekday
from app.modules.player_profile.domain.weekly_hours import (
    HOURS_OF_THE_DAY,
    WeeklyHour,
    WeeklyHours,
)

EVERY_HOUR_OF_THE_WEEK = [(day, hour) for day in range(1, 8) for hour in range(24)]

A_REAL_WEEK = [
    (1, 19),
    (1, 20),
    (2, 19),
    (2, 20),
    (3, 7),
    (4, 21),
    (6, 10),
    (6, 11),
    (6, 12),
    (7, 17),
    (7, 18),
]


def scanned(week: WeeklyHours, day: int, hour: int) -> bool:
    """The definition this replaced: a scan over every ticked cell."""

    return any(int(cell.day) == day and cell.hour == hour for cell in week.hours)


@pytest.mark.parametrize(
    "cells",
    [
        pytest.param([], id="empty"),
        pytest.param([(2, 19)], id="one hour"),
        pytest.param(
            [(day, hour) for day in range(1, 8) for hour in HOURS_OF_THE_DAY],
            id="every hour",
        ),
        pytest.param(A_REAL_WEEK, id="a real one"),
    ],
)
def test_every_hour_of_the_week_is_answered_as_the_scan_answered_it(cells) -> None:
    week = WeeklyHours.edited(cells)

    for day, hour in EVERY_HOUR_OF_THE_WEEK:
        assert week.holds(iso_weekday(day), hour) is scanned(week, day, hour)


def test_an_hour_outside_the_grid_is_simply_not_ticked() -> None:
    week = WeeklyHours.edited(
        [(day, hour) for day in range(1, 8) for hour in HOURS_OF_THE_DAY]
    )

    for day in range(1, 8):
        for hour in (0, 6, 23, 24, -1, 99):
            assert week.holds(iso_weekday(day), hour) is False


def test_the_week_is_the_same_value_whichever_way_it_was_built() -> None:
    """Equality, order, codes and cells are the week's; the lookup is derived
    from them and is no part of what two weeks are compared on."""

    edited = WeeklyHours.edited(reversed(A_REAL_WEEK))
    of_cells = WeeklyHours.of_cells(A_REAL_WEEK)
    from_codes = WeeklyHours.from_codes(of_cells.codes)
    of_hours = WeeklyHours.of(WeeklyHour(iso_weekday(d), h) for d, h in A_REAL_WEEK)

    assert edited == of_cells == from_codes == of_hours
    assert len({edited, of_cells, from_codes, of_hours}) == 1
    assert edited.cells == tuple(sorted(A_REAL_WEEK))
    assert edited.codes == tuple(f"{d}:{h}" for d, h in sorted(A_REAL_WEEK))
    assert "ticked" not in repr(edited)
    assert WeeklyHours.blank() == WeeklyHours.edited([]) == WeeklyHours()


def test_a_week_rebuilt_or_pickled_still_answers_by_lookup() -> None:
    """`replace` and pickling go round the constructor; the lookup must come
    back with the week rather than be left behind."""

    week = WeeklyHours.edited(A_REAL_WEEK)

    rebuilt = replace(week)
    unpickled = pickle.loads(pickle.dumps(week))

    assert rebuilt == unpickled == week
    for day, hour in EVERY_HOUR_OF_THE_WEEK:
        assert rebuilt.holds(iso_weekday(day), hour) is scanned(week, day, hour)
        assert unpickled.holds(iso_weekday(day), hour) is scanned(week, day, hour)


def test_the_lookup_is_derived_once_per_week_and_not_rebuilt_per_question() -> None:
    week = WeeklyHours.edited(A_REAL_WEEK)

    first = week.ticked
    for day, hour in EVERY_HOUR_OF_THE_WEEK:
        week.holds(iso_weekday(day), hour)

    assert week.ticked is first
    assert week.ticked == frozenset(A_REAL_WEEK)
