"""The overlap grid a group-deck card draws, and its grade (the mechanics §8.1,
the screens A2.3; Q71).

**The people on the card's week, summarised as 7 days × 3 ranges** — Morning
07–12, Afternoon 12–17, Evening 17–23, the ranges ``weekly_hours.py`` names
beside the hours they group. It is the one place a week is drawn as a calendar,
and what it draws is never one person's week: a cell says how many of them are
free **together**, never who.

**Together means at one hour.** A cell is *bright* where everybody on the card
is free for one whole hour of the range, *dim* where all but one are, and dark
otherwise — read hour by hour and never range by range, because four people free
on a Tuesday morning at four different hours cannot play on Tuesday morning (the
same rule the posting grid counts by, Q92). *All but one* means something only
on a card with three people or more: on a singles card it would be *one of the
two*, which is a fact about one person's week, so a two-person card is bright or
dark.

**The grade is the engine's reading, cut three ways.** ``group_availability``
is the engine's reading of a court's week — the hours everybody shares, over
the week of whoever has least to give — and a card reads that number rather
than inventing a second measure of *overlap*. *High* from half, *Good* from a
quarter, *Slim* below; a blank week on the card stands the engine's reading down,
and a card with nothing known about somebody's week is *Slim*, never *High*.
These two cut points were set with this card, for its label alone: nothing
ranks, deals or refuses on them.

**Pure**: the weeks, the game's start and the zone its wall clock is read in.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, final

from app.engines.matchfit.scorable import GridCell
from app.engines.matchfit.v1 import group_availability
from app.kernel import (
    Instant,
    Zone,
    invariant,
    iso_weekday,
    local_iso_weekday,
    local_minute_of_day,
)
from app.modules.player_profile.domain.weekly_hours import (
    DAY_RANGES,
    DAYS_IN_THE_GRID,
    WeeklyHours,
)

#: From this share of the narrowest week shared by everybody, the overlap is
#: *High*; from the second, *Good*; below it, *Slim*.
HIGH_FROM: Final = 0.5
GOOD_FROM: Final = 0.25


class DayRange(StrEnum):
    """A third of a day, as a card and the posting grid group hours."""

    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"


# The names are ``weekly_hours.py``'s, so the two cannot drift apart.
invariant(
    tuple(DAY_RANGES) == tuple(DayRange),
    f"the day's ranges are {tuple(DAY_RANGES)}",
)


class OverlapShade(StrEnum):
    """How many of the card's people are free together in a cell."""

    #: Everybody.
    BRIGHT = "BRIGHT"
    #: All but one — on a card of three or more.
    DIM = "DIM"
    #: Fewer.
    DARK = "DARK"


class OverlapGrade(StrEnum):
    HIGH = "HIGH"
    GOOD = "GOOD"
    SLIM = "SLIM"


@final
@dataclass(frozen=True, slots=True)
class OverlapCell:
    #: The ISO weekday, Monday first.
    day: int
    range: DayRange
    shade: OverlapShade


@final
@dataclass(frozen=True, slots=True)
class GameCell:
    """The cell the game itself is in — ringed on the card."""

    day: int
    range: DayRange


@final
@dataclass(frozen=True, slots=True)
class Overlap:
    grade: OverlapGrade
    #: Twenty-one cells, day by day and, within a day, morning first.
    cells: tuple[OverlapCell, ...]
    game: GameCell


def overlap_of(weeks: Sequence[WeeklyHours], *, start: Instant, zone: Zone) -> Overlap:
    """The grid and the grade for the people whose ``weeks`` these are, and the
    game at ``start`` — its day and hour read on ``zone``'s wall clock."""

    invariant(len(weeks) > 0, "an overlap of nobody's week")
    return Overlap(
        grade=_grade(weeks),
        cells=tuple(
            OverlapCell(day=day, range=range_, shade=_shade(weeks, day, range_))
            for day in range(1, DAYS_IN_THE_GRID + 1)
            for range_ in DayRange
        ),
        game=_game_cell(start, zone),
    )


def _shade(weeks: Sequence[WeeklyHours], day: int, range_: DayRange) -> OverlapShade:
    weekday = iso_weekday(day)
    together = max(
        sum(1 for week in weeks if week.holds(weekday, hour))
        for hour in DAY_RANGES[range_.value]
    )
    if together == len(weeks):
        return OverlapShade.BRIGHT
    if len(weeks) >= 3 and together == len(weeks) - 1:
        return OverlapShade.DIM
    return OverlapShade.DARK


def _grade(weeks: Sequence[WeeklyHours]) -> OverlapGrade:
    shared = group_availability(
        [
            tuple(GridCell(day=cell.day, hour=cell.hour) for cell in week.hours)
            for week in weeks
        ]
    )
    if shared is None:
        return OverlapGrade.SLIM
    if shared >= HIGH_FROM:
        return OverlapGrade.HIGH
    if shared >= GOOD_FROM:
        return OverlapGrade.GOOD
    return OverlapGrade.SLIM


def _game_cell(start: Instant, zone: Zone) -> GameCell:
    hour = int(local_minute_of_day(start, zone)) // 60
    range_ = next(
        (DayRange(name) for name, hours in DAY_RANGES.items() if hour in hours),
        None,
    )
    invariant(range_ is not None, f"a court hour at {hour}:00, outside every range")
    assert range_ is not None
    return GameCell(day=int(local_iso_weekday(start, zone)), range=range_)
