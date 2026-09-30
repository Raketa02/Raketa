"""Weekly hours: an ordinary week, seven days by sixteen hours.

A player says when they are free by ticking one-hour cells of a **7 × 16**
grid, Monday-first, from 07:00 to 23:00 (``../../../../CONTEXT.md`` — *Weekly
hours*; the mechanics §4.2). It replaced the 7 days × morning / afternoon /
evening grid with ``docs/adr/0189`` §5, because a court is booked by the hour
and a third of a day is not a precision a real court hour can be read against.
It is the only way time preference is ever expressed here, and it is still a
**preference, not a promise** — a ticked hour is never a commitment or a hold;
what it now also is, is the thing a court hour is **read against**
(:func:`free_for_the_hour`).

**The week is required, and its floor is exactly one hour of the 112**
(``docs/adr/0102``, amended by ``docs/adr/0189``). This is a sport application;
when a player usually plays is not optional information. One tick is a real
answer — a player who only ever plays at ten on a Saturday must be able to say
precisely that, and the near-total absence of overlap that follows is a
**measured** near-zero. A higher minimum would be the platform telling people
what their week looks like.

**A blank week met anyway is *absent*, never zero.** Requiring the field at
commit does not make blank weeks impossible: a player may clear their week
afterwards. Where one is encountered, the matcher's availability term stands down
with no evidence rather than scoring a nought — because the player never said
they are never free, they said nothing, and *an unanswered field is never a
negative filter*. That neighbour survives and is now kept by construction rather
than by weighing: the floor removes the unanswered case at the only place a
player answers.

Which is why the floor lives in ``of_cells`` and nowhere else. ``of``, ``blank``
and ``from_codes`` must keep taking an empty week, or a rule adopted today would
retroactively refuse to rehydrate a profile that was legal when it was written.

``social_tags`` states that split as *"the write path refuses; the fold accepts"*,
and here it is narrower than that: **the commit path refuses.**
``PlayerProfile.set_weekly_hours`` is a write too, and it accepts a blank week
deliberately — a player may clear their week after committing, and the minimum
binds the answer they are asked for rather than every later edit of it. That
counterpart has a name: ``edited`` takes the same primitives as ``of_cells`` and
enforces no floor, so the edit path is a constructor a reader can see rather than
an asymmetry they have to infer.

**A search's improvised week is an edit and not an answer**, so it builds through
``edited`` too. That is the sentence above read literally rather than loosely:
*the commit path* is one route, and a player who unticks every hour on the Play
screen and searches is not on it.

**The floor is not served.** Unlike the tag floor and ceiling it is fixed by the
record rather than by product, so a client holds it as a constant the way it
holds the photo cap, and ``GET /player-profile/options`` does not carry it. Nor
are the grid's edges: 07:00 and 23:00 are the mechanics' own, and a client draws
the same sixteen rows.

**The day is the kernel's ``IsoWeekday``**, not a weekday enum of this context's
own. Monday-first is already what ISO means, and a second spelling of the days of
the week is exactly the kind of duplicate vocabulary the shared kernel exists to
prevent. **The hour is a plain integer, the hour a cell starts at**: the cell
``(2, 19)`` is Tuesday 19:00–20:00, wall clock, in whatever zone the court hour it
is read against is in. A week holds no zone of its own, because the zone is the
court's and a player's week means the same local evening wherever they play.

**The grid is never rendered to anybody as a calendar.** Only the count of shared
hours and the name of the next shared one are ever shown, because overlap is a
fact about a pair where a calendar is a fact about a person. Nothing in this
module serves one; the invariant is recorded here so that the first thing that
tries has to argue with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Iterable, Mapping

from app.kernel import (
    Instant,
    IsoWeekday,
    Zone,
    invariant,
    iso_weekday,
    local_iso_weekday,
    local_minute_of_day,
)
from app.modules.player_profile.domain.errors import WeeklyHoursEmpty

#: How many days the grid covers. Named rather than written as ``7`` at each use
#: so that "the ordinary week" is one fact and not four.
DAYS_IN_THE_GRID: Final = 7

#: The hour the grid's first cell starts at — 07:00 (the mechanics §4.2).
FIRST_HOUR: Final = 7

#: The hour the grid's **last** cell starts at. The grid ends at 23:00, so the
#: last cell is 22:00–23:00 and there is no cell starting at 23.
LAST_HOUR: Final = 22

#: Every hour a cell may start at, in the order a day is laid out. A tuple so a
#: caller can index and count it; sixteen of them.
HOURS_OF_THE_DAY: Final = tuple(range(FIRST_HOUR, LAST_HOUR + 1))

#: The three ranges a day's hours are grouped into wherever a week is summarised
#: rather than drawn whole — the card's overlap grid and the posting grid (the
#: mechanics §9.1, Q71): Morning 07–12, Afternoon 12–17, Evening 17–23. Named
#: here, beside the hours they group, so that whatever groups them holds no copy
#: of where one ends. **A summary and never a cell**: nothing is stored in a
#: range, and a range is not what a player ticks.
DAY_RANGES: Final[Mapping[str, tuple[int, ...]]] = {
    "MORNING": tuple(range(FIRST_HOUR, 12)),
    "AFTERNOON": tuple(range(12, 17)),
    "EVENING": tuple(range(17, LAST_HOUR + 1)),
}

#: The separator inside a cell's durable code. A colon because neither half can
#: contain one, so splitting is unambiguous forever.
_CODE_SEPARATOR: Final = ":"

#: Minutes in the hour a court hour lasts. Every game is one hour
#: (``docs/adr/0189`` §3); named for the arithmetic below, not as a setting.
_AN_HOUR: Final = 60


@dataclass(frozen=True, slots=True)
class WeeklyHour:
    """One cell: a day of the ordinary week, and the hour it starts at."""

    day: IsoWeekday
    hour: int

    def __post_init__(self) -> None:
        # Through the kernel's own factory, so 0, 8 and ``True`` are refused
        # here exactly as they are refused anywhere else a weekday is built.
        iso_weekday(int(self.day))
        invariant(
            not isinstance(self.hour, bool) and self.hour in HOURS_OF_THE_DAY,
            f"an hour outside the week's {FIRST_HOUR}:00–{LAST_HOUR + 1}:00: "
            f"{self.hour!r}",
        )

    @property
    def in_reading_order(self) -> tuple[int, int]:
        """This cell's place in the week — day first, then hour.

        A week sorts on this so that it has one canonical arrangement: two
        players who ticked the same hours hold equal weeks whatever order their
        clients sent them in.
        """

        return int(self.day), self.hour

    @property
    def code(self) -> str:
        """The cell as one string, which is how a stream stores it — ``"2:19"``.

        A single field rather than a nested pair because the event codec coerces
        only scalars: a ``tuple[tuple[int, int], ...]`` would come back out of
        storage as lists of lists, and the aggregate would be rebuilding the
        shape on every replay. One string round-trips as itself.
        """

        return f"{int(self.day)}{_CODE_SEPARATOR}{self.hour}"

    @classmethod
    def from_code(cls, code: str) -> "WeeklyHour":
        """The cell a stored ``code`` names.

        Raises through ``invariant`` rather than returning a refusal, because
        this reads *history*: a code this cannot parse is a corrupt stream or a
        codec that changed under it, and neither is a state a caller can recover
        from by asking the player again. A part of the day stored before the
        week became hours — ``"2:EVENING"`` — is one of them: nothing ran
        anywhere but ``local``, so there is no history to translate
        (``docs/adr/0189`` §5).
        """

        day, _, hour = code.partition(_CODE_SEPARATOR)
        invariant(day.isdigit() and hour.isdigit(), f"weekly hour code: {code!r}")
        return cls(day=iso_weekday(int(day)), hour=int(hour))


@dataclass(frozen=True, slots=True)
class WeeklyHours:
    """The hours a player ticked, deduplicated and in one canonical order.

    Constructed through ``of`` rather than directly, so that no caller holds a
    week whose order or duplicates are its own. Duplicates are **dropped** rather
    than refused — the week is a set of hours, and a client that sent Tuesday
    19:00 twice ticked Tuesday 19:00, which is not an ambiguity anybody needs
    resolving.
    """

    hours: tuple[WeeklyHour, ...] = ()

    def __post_init__(self) -> None:
        invariant(
            list(self.hours) == _in_reading_order(self.hours),
            "a week of hours was built outside `of`",
        )

    @classmethod
    def of(cls, hours: Iterable[WeeklyHour]) -> "WeeklyHours":
        return cls(hours=tuple(_in_reading_order(set(hours))))

    @classmethod
    def blank(cls) -> "WeeklyHours":
        """A week with nothing ticked. **Not a way past the floor.**

        No commit path reaches this: ``of_cells`` is what a player's answer
        arrives through and it refuses an empty week. What this is for is a week
        that has to exist without being an answer — a player who clears their
        week afterwards. A week built here means *we do not know*, and the
        matcher reads it that way (ADR-0102 part 3).
        """

        return cls()

    @classmethod
    def of_cells(cls, cells: Iterable[tuple[int, int]]) -> "WeeklyHours":
        """The week these ``(weekday, hour)`` pairs make. **At least one.**

        The commit path's entry point, so that a *command* carries primitives
        from the boundary and the domain is what turns them into hours
        (``backend/CONTEXT.md`` — *Command*).

        **This is the one place the floor is enforced**, because it is the one
        place the answer a player was *asked for* arrives. Nothing ticked is
        refused with ``WeeklyHoursEmpty`` — a *refusal* rather than a broken
        precondition, because it is a legitimate thing for a client to send and
        the client's recovery is to go back to the week and tick an hour.

        Counted **after** the fold, so a client that sent Tuesday 19:00 three
        times is at one and not at three: the count is of hours, which is what
        the player ticked, and never of what arrived.
        """

        week = cls.edited(cells)
        if not week.hours:
            raise WeeklyHoursEmpty()
        return week

    @classmethod
    def edited(cls, cells: Iterable[tuple[int, int]]) -> "WeeklyHours":
        """The week a player just edited. **The floor's named exit.**

        The same ``(weekday, hour)`` primitives ``of_cells`` takes and the same
        fold, minus the minimum — because *the commit path refuses* is this
        module's rule and a later edit is not the commit. A player may clear
        their week afterwards, and ``PlayerProfile.set_weekly_hours`` accepts a
        blank week.

        **Two callers, and neither is a commit**: the weekly-hours write route,
        and a search's ``availability_override`` — the week a player improvised
        for one evening, on any of the three surfaces that take one. Both are
        edits of an answer already given, which is exactly what the floor does
        not bind.

        **Named rather than a flag on ``of_cells``**, which is
        ``SearchRadius.chosen`` / ``recorded``'s discipline applied to the week:
        every call site says which of the two it is, where a flag re-asks the
        question at each of them and makes the wrong answer the shorter one. It
        is not ``from_codes`` either — that is the **replay** constructor, and
        building a player's live edit through it is a category error.

        Raises through ``invariant`` for a pair that is not a cell, exactly as
        ``of_cells`` does: the boundary schema constrains the day to 1–7 and the
        hour to the sixteen there are, so reaching this with anything else means
        a caller inside the application built it.
        """

        return cls.of(
            WeeklyHour(day=iso_weekday(day), hour=hour) for day, hour in cells
        )

    @classmethod
    def from_codes(cls, codes: Iterable[str]) -> "WeeklyHours":
        return cls.of(WeeklyHour.from_code(code) for code in codes)

    @property
    def cells(self) -> tuple[tuple[int, int], ...]:
        """The week as the boundary spells it, in the week's own order."""

        return tuple((int(cell.day), cell.hour) for cell in self.hours)

    @property
    def codes(self) -> tuple[str, ...]:
        """The week as a stream stores it, in the week's own order."""

        return tuple(cell.code for cell in self.hours)

    def holds(self, day: IsoWeekday, hour: int) -> bool:
        """Whether the hour starting at ``hour`` on ``day`` is ticked.

        An hour outside the grid is simply not held, rather than a broken
        precondition: *is 23:00 free* is a question a court hour at 22:30 asks
        honestly, and the answer is no.
        """

        return any(
            int(cell.day) == int(day) and cell.hour == hour for cell in self.hours
        )

    def __len__(self) -> int:
        return len(self.hours)


def free_for_the_hour(week: WeeklyHours, *, start: Instant, zone: Zone) -> bool:
    """Whether a player with ``week`` is free for the court hour from ``start``.

    **Only when the whole hour is inside their weekly hours** — never when merely
    its start is (the mechanics §4.2, ``docs/adr/0189`` §5). This is the one
    function the rule lives in: the proposer, posting and the rescue board ask it
    here rather than re-deriving it, so three readings of one week cannot come to
    two answers about one hour.

    ``start`` is an instant, because every court hour is stored in UTC, and
    ``zone`` is where the court is — the week is wall clock, so the weekday and
    the hour are read **in that zone**, through the kernel, and never off the
    instant's own UTC date. Start times are the club's own, so a start need not
    be on the hour: 19:30 runs to 20:30 and needs both 19:00 and 20:00 ticked.

    Read on the wall clock rather than in elapsed minutes, deliberately: the only
    local hours a clock change can bend are between 02:00 and 03:00, and the grid
    starts at seven.

    **A blank week is free for nothing.** It is *absent* to the overlap term
    (ADR-0102), and being free is a claim a week has to make — a week that says
    nothing makes none.
    """

    day = local_iso_weekday(start, zone)
    first, past_the_hour = divmod(int(local_minute_of_day(start, zone)), _AN_HOUR)
    straddled = (first,) if past_the_hour == 0 else (first, first + 1)
    return all(week.holds(day, hour) for hour in straddled)


def _in_reading_order(hours: Iterable[WeeklyHour]) -> list[WeeklyHour]:
    return sorted(hours, key=lambda cell: cell.in_reading_order)


#: A single day carrying at most this many hours reads as a **window on that
#: day** rather than as a week. Adopted from the prototype as a starting position
#: (``docs/adr/0100`` §6) at *two parts of a day's three*, and carried over to
#: hours as the same share of sixteen, rounded down — so no threshold claims more
#: of a day than it did (``docs/adr/0100``, amended by ``docs/adr/0189``). Its
#: falsifier is unchanged: the rate at which a challenge is answered with a
#: counter-proposal outside its stated window, and a label carrying no
#: information is **removed rather than tuned**.
WINDOW_SINGLE_DAY_MAX_HOURS: Final = 2 * len(HOURS_OF_THE_DAY) // 3

#: At or above this many hours over the whole week, no window is narrower than
#: *any*. Same provenance and the same falsifier: *twelve cells of twenty-one*,
#: carried over as the same share of the week's 112 hours.
WINDOW_ANY_MIN_HOURS: Final = 12 * DAYS_IN_THE_GRID * len(HOURS_OF_THE_DAY) // 21

#: Saturday and Sunday. **A locale assumption, recorded as one rather than as a
#: constant to tune** (``docs/adr/0100`` §7) — it is not a number, and its
#: falsifier is the first shard whose weekend is somewhere else.
_WEEKEND = frozenset({6, 7})


class Window(StrEnum):
    """When a game found on a week would plausibly be played. **A code, never a
    sentence** — *"tonight"* is the client's word (``docs/adr/0022``).

    **Derived, never chosen** (``docs/adr/0100``). There is no window picker
    anywhere: a player changes their window by changing their week, which is the
    same act that changes their matches. One control, one meaning.

    It is a **label on the search**, not a proposed time — the week is still
    never rendered to anybody as a calendar, and this says only how soon the week
    it ran on comes round.
    """

    TODAY = "TODAY"
    TOMORROW = "TOMORROW"
    WEEKEND = "WEEKEND"
    THIS_WEEK = "THIS_WEEK"
    ANY = "ANY"


def window_of(week: WeeklyHours, today: IsoWeekday) -> Window:
    """The window a search run on this week is asking about.

    ``docs/adr/0100`` §4 puts the function here, beside the week, and hands the
    caller the one thing this module refuses to know: **what day it is.**
    ``IsoWeekday`` is kernel vocabulary and is neither a date nor a timezone.

    The ladder is read narrowest-first, and every rung is a statement about the
    **week**, never about the pair:

    - a wide-open week says nothing about when, and reads ``ANY``;
    - a week ticked on one day alone, lightly, is that day — *today*,
      *tomorrow*, or simply *this week* when it is further off;
    - a week ticked only across Saturday and Sunday is the weekend;
    - anything else is this week.

    An empty week reads ``ANY``. A blank week means *we do not know* rather than
    *never*, and *any* is the only rung that claims nothing.
    """

    days = {int(cell.day) for cell in week.hours}
    if not days or len(week) >= WINDOW_ANY_MIN_HOURS:
        return Window.ANY
    if len(days) == 1 and len(week) <= WINDOW_SINGLE_DAY_MAX_HOURS:
        return _single_day(next(iter(days)), int(today))
    if days <= _WEEKEND:
        return Window.WEEKEND
    return Window.THIS_WEEK


def _single_day(day: int, today: int) -> Window:
    """Which of the three near rungs one ticked day lands on.

    *Tomorrow* wraps the week — Sunday's tomorrow is Monday — because the week is
    an **ordinary** week and has no notion of a particular one. Anything further
    off than tomorrow is ``THIS_WEEK`` rather than a count of days: a number of
    days is a date, and this module holds none.
    """

    if day == today:
        return Window.TODAY
    if day == today % DAYS_IN_THE_GRID + 1:
        return Window.TOMORROW
    return Window.THIS_WEEK
