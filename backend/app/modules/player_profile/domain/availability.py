"""The availability grid: an ordinary week, seven days by three parts.

A player says when they usually want to play by ticking cells of a **7 × 3**
grid, Monday-first (``../../../../CONTEXT.md``). It is the only way time
preference is ever expressed here, and it is a **preference, not a promise** — a
ticked slot is never a commitment, a hold, or a bookable time, which is why
nothing in this module has a duration, a date or a timezone in it.

**The grid is required, and its floor is exactly one cell of the twenty-one**
(``docs/adr/0102``). This is a sport application; when a player usually plays is
not optional information. One tick is a real answer — a player who only ever
plays Saturday mornings must be able to say precisely that, and the near-total
absence of overlap that follows is a **measured** near-zero. A higher minimum
would be the platform telling people what their week looks like.

**A blank grid met anyway is *absent*, never zero.** Requiring the field at
commit does not make blank grids impossible: a player may clear their week
afterwards, and profiles committed before the floor existed still hold one.
Where one is encountered, the matcher's availability term stands down with no
evidence rather than scoring a nought — because the player never said they are
never free, they said nothing, and *an unanswered field is never a negative
filter*. That neighbour survives and is now kept by construction rather than by
weighing: the floor removes the unanswered case at the only place a player
answers.

Which is why the floor lives in ``of_cells`` and nowhere else. ``of``, ``blank``
and ``from_codes`` must keep taking an empty grid, or a rule adopted today would
retroactively refuse to rehydrate a profile that was legal when it was written.

``social_tags`` states that split as *"the write path refuses; the fold accepts"*,
and here it is narrower than that: **the commit path refuses.**
``PlayerProfile.change_availability`` is a write too, and it accepts a blank grid
deliberately — a player may clear their week after committing, and the minimum
binds the answer they are asked for rather than every later edit of it. That
counterpart now has a name: ``edited`` takes the same primitives as ``of_cells``
and enforces no floor, so the edit path is a constructor a reader can see rather
than an asymmetry they have to infer.

**A search's improvised week is an edit and not an answer**, so it builds through
``edited`` too. That is the sentence above read literally rather than loosely:
*the commit path* is one route, and a player who unticks every cell on the Play
screen and searches is not on it. Building a search override through ``of_cells``
enforced the floor a layer out from this module and refused them a `400`; a grid
this module hands out blank cannot be one a matcher refuses to run on.

**The floor is not served.** Unlike the tag floor and ceiling it is fixed by the
record rather than by product, so a client holds it as a constant the way it
holds the photo cap, and ``GET /player-profile/options`` does not carry it.

**The day is the kernel's ``IsoWeekday``**, not a weekday enum of this context's
own. Monday-first is already what ISO means, and a second spelling of the days of
the week is exactly the kind of duplicate vocabulary the shared kernel exists to
prevent. The *part* is this context's own: morning, afternoon and evening are the
finest precision this product holds, and nothing outside a profile has an opinion
about them.

**The grid is never rendered to anybody as a calendar.** Only the count of shared
slots and the name of the next shared one are ever shown, because overlap is a
fact about a pair where a calendar is a fact about a person. Nothing in this
module serves one; the invariant is recorded here so that the first thing that
tries has to argue with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Iterable

from app.kernel import IsoWeekday, invariant, iso_weekday
from app.modules.player_profile.domain.errors import AvailabilityGridEmpty

#: How many days the grid covers. Named rather than written as ``7`` at each use
#: so that "the ordinary week" is one fact and not four.
DAYS_IN_THE_GRID: Final = 7


class DayPart(StrEnum):
    """The three parts of a day a player may tick.

    Closed, and deliberately coarse. The product asks *when do you usually play*,
    and an answer finer than this would be a schedule — which is the thing a
    preference is explicitly not.

    Declared in rendering order, so ``tuple(DayPart)`` is the order a grid is
    laid out in and no caller sorts.
    """

    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"


#: The separator inside a slot's durable code. A colon rather than an underscore
#: because neither half can contain one, so splitting is unambiguous forever.
_CODE_SEPARATOR: Final = ":"


#: Where each part sits in a day, so a grid sorts into reading order. Needed
#: because ``DayPart`` is a ``StrEnum`` and comparing two of them compares their
#: *text* — which would file an afternoon before a morning.
_PART_ORDER: Final = {part: position for position, part in enumerate(DayPart)}


@dataclass(frozen=True, slots=True)
class AvailabilitySlot:
    """One cell: a day of the ordinary week, and one part of it."""

    day: IsoWeekday
    part: DayPart

    def __post_init__(self) -> None:
        # Through the kernel's own factory, so 0, 8 and ``True`` are refused
        # here exactly as they are refused anywhere else a weekday is built.
        iso_weekday(int(self.day))

    @property
    def in_reading_order(self) -> tuple[int, int]:
        """This slot's place in the week — day first, then part of day.

        A grid sorts on this so that it has one canonical arrangement: two
        players who ticked the same cells hold equal grids whatever order their
        clients sent them in.
        """

        return int(self.day), _PART_ORDER[self.part]

    @property
    def code(self) -> str:
        """The slot as one string, which is how a stream stores it.

        A single field rather than a nested pair because the event codec coerces
        only scalars: a ``tuple[tuple[int, str], ...]`` would come back out of
        storage as lists of lists, and the aggregate would be rebuilding the
        shape on every replay. One string round-trips as itself.
        """

        return f"{int(self.day)}{_CODE_SEPARATOR}{self.part.value}"

    @classmethod
    def from_code(cls, code: str) -> "AvailabilitySlot":
        """The slot a stored ``code`` names.

        Raises through ``invariant`` rather than returning a refusal, because
        this reads *history*: a code this cannot parse is a corrupt stream or a
        codec that changed under it, and neither is a state a caller can recover
        from by asking the player again.
        """

        day, _, part = code.partition(_CODE_SEPARATOR)
        invariant(day.isdigit(), f"availability slot code: {code!r}")
        invariant(part in DayPart.__members__, f"availability slot code: {code!r}")
        return cls(day=iso_weekday(int(day)), part=DayPart[part])


@dataclass(frozen=True, slots=True)
class AvailabilityGrid:
    """The cells a player ticked, deduplicated and in one canonical order.

    Constructed through ``of`` rather than directly, so that no caller holds a
    grid whose order or duplicates are its own. Duplicates are **dropped** rather
    than refused — the grid is a set of cells, and a client that sent Tuesday
    morning twice ticked Tuesday morning, which is not an ambiguity anybody needs
    resolving.
    """

    slots: tuple[AvailabilitySlot, ...] = ()

    def __post_init__(self) -> None:
        invariant(
            list(self.slots) == _in_reading_order(self.slots),
            "an availability grid was built outside `of`",
        )

    @classmethod
    def of(cls, slots: Iterable[AvailabilitySlot]) -> "AvailabilityGrid":
        return cls(slots=tuple(_in_reading_order(set(slots))))

    @classmethod
    def blank(cls) -> "AvailabilityGrid":
        """A week with nothing ticked. **Not a way past the floor.**

        No commit path reaches this: ``of_cells`` is what a player's answer
        arrives through and it refuses an empty grid. What this is for is a grid
        that has to exist without being an answer — a profile that held one
        before the floor did, and a player who clears their week afterwards. A
        grid built here means *we do not know*, and the matcher reads it that way
        (ADR-0102 part 3).
        """

        return cls()

    @classmethod
    def of_cells(cls, cells: Iterable[tuple[int, str]]) -> "AvailabilityGrid":
        """The grid these ``(weekday, part)`` pairs make. **At least one.**

        The commit path's entry point, so that a *command* carries primitives
        from the boundary and the domain is what turns them into slots
        (``backend/CONTEXT.md`` — *Command*).

        **This is the one place the floor is enforced**, because it is the one
        place the answer a player was *asked for* arrives. Nothing ticked is
        refused with ``AvailabilityGridEmpty`` — a *refusal* rather than a broken
        precondition, because it is a legitimate thing for a client to send and
        the client's recovery is to go back to the week and tick a cell.

        Counted **after** the fold, so a client that sent Tuesday morning three
        times is at one and not at three: the count is of cells, which is what
        the player ticked, and never of what arrived.
        """

        grid = cls.edited(cells)
        if not grid.slots:
            raise AvailabilityGridEmpty()
        return grid

    @classmethod
    def edited(cls, cells: Iterable[tuple[int, str]]) -> "AvailabilityGrid":
        """The grid a player just edited. **The floor's named exit.**

        The same ``(weekday, part)`` primitives ``of_cells`` takes and the same
        fold, minus the minimum — because *the commit path refuses* is this
        module's rule and a later edit is not the commit. A player may clear
        their week afterwards, and ``PlayerProfile.change_availability`` has
        always accepted a blank grid; until this existed there was no boundary
        constructor that could hand it one.

        **Two callers, and neither is a commit**: the availability write route,
        and a search's ``availability_override`` — the week a player improvised
        for one evening, on any of the three surfaces that take one. Both are
        edits of an answer already given, which is exactly what the floor does
        not bind.

        **Named rather than a flag on ``of_cells``**, which is
        ``SearchRadius.chosen`` / ``recorded``'s discipline applied to the grid:
        every call site says which of the two it is, where a flag re-asks the
        question at each of them and makes the wrong answer the shorter one. It
        is not ``from_codes`` either — that is the **replay** constructor, and
        building a player's live edit through it is a category error.

        Raises through ``invariant`` for a pair that is not a cell, exactly as
        ``of_cells`` does: the boundary schema constrains the day to 1–7 and the
        part to the three there are, so reaching this with anything else means a
        caller inside the application built it.
        """

        return cls.of(
            AvailabilitySlot(day=iso_weekday(day), part=_part(part))
            for day, part in cells
        )

    @classmethod
    def from_codes(cls, codes: Iterable[str]) -> "AvailabilityGrid":
        return cls.of(AvailabilitySlot.from_code(code) for code in codes)

    @property
    def cells(self) -> tuple[tuple[int, str], ...]:
        """The grid as the boundary spells it, in the grid's own order."""

        return tuple((int(slot.day), slot.part.value) for slot in self.slots)

    @property
    def codes(self) -> tuple[str, ...]:
        """The grid as a stream stores it, in the grid's own order."""

        return tuple(slot.code for slot in self.slots)

    def __len__(self) -> int:
        return len(self.slots)


def _part(value: str) -> DayPart:
    invariant(value in DayPart.__members__, f"part of the day: {value!r}")
    return DayPart[value]


def _in_reading_order(
    slots: Iterable[AvailabilitySlot],
) -> list[AvailabilitySlot]:
    return sorted(slots, key=lambda slot: slot.in_reading_order)


#: A single day carrying at most this many ticks reads as a **window on that
#: day** rather than as a week. Adopted from the prototype as a starting
#: position (``docs/adr/0100`` §6); its falsifier is the rate at which a
#: challenge is answered with a counter-proposal outside its stated window, and
#: a label carrying no information is **removed rather than tuned**.
WINDOW_SINGLE_DAY_MAX_SLOTS: Final = 2

#: At or above this many ticks over the whole grid, no window is narrower than
#: *any*. Same provenance and the same falsifier.
WINDOW_ANY_MIN_SLOTS: Final = 12

#: Saturday and Sunday. **A locale assumption, recorded as one rather than as a
#: constant to tune** (``docs/adr/0100`` §7) — it is not a number, and its
#: falsifier is the first shard whose weekend is somewhere else.
_WEEKEND = frozenset({6, 7})


class Window(StrEnum):
    """When a game found on a grid would plausibly be played. **A code, never a
    sentence** — *"tonight"* is the client's word (``docs/adr/0022``).

    **Derived, never chosen** (``docs/adr/0100``). There is no window picker
    anywhere: a player changes their window by changing their grid, which is the
    same act that changes their matches. One control, one meaning.

    It is a **label on the search**, not a proposed time — the grid is still
    never rendered to anybody as a calendar, and this says only how soon the week
    it ran on comes round.
    """

    TODAY = "TODAY"
    TOMORROW = "TOMORROW"
    WEEKEND = "WEEKEND"
    THIS_WEEK = "THIS_WEEK"
    ANY = "ANY"


def window_of(grid: AvailabilityGrid, today: IsoWeekday) -> Window:
    """The window a search run on this grid is asking about.

    ``docs/adr/0100`` §4 puts the function here, beside the grid, and hands the
    caller the one thing this module refuses to know: **what day it is.**
    ``IsoWeekday`` is kernel vocabulary and is neither a date nor a timezone, so
    the module's negative space — *nothing here has a duration, a date or a
    timezone in it* — is intact.

    The ladder is read narrowest-first, and every rung is a statement about the
    **grid**, never about the pair:

    - a wide-open week says nothing about when, and reads ``ANY``;
    - a grid ticked on one day alone, lightly, is that day — *today*, *tomorrow*,
      or simply *this week* when it is further off;
    - a grid ticked only across Saturday and Sunday is the weekend;
    - anything else is this week.

    An empty grid reads ``ANY``. A blank grid means *we do not know* rather than
    *never*, and *any* is the only rung that claims nothing.
    """

    days = {int(slot.day) for slot in grid.slots}
    if not days or len(grid) >= WINDOW_ANY_MIN_SLOTS:
        return Window.ANY
    if len(days) == 1 and len(grid) <= WINDOW_SINGLE_DAY_MAX_SLOTS:
        return _single_day(next(iter(days)), int(today))
    if days <= _WEEKEND:
        return Window.WEEKEND
    return Window.THIS_WEEK


def _single_day(day: int, today: int) -> Window:
    """Which of the three near rungs one ticked day lands on.

    *Tomorrow* wraps the week — Sunday's tomorrow is Monday — because the grid is
    an **ordinary** week and has no notion of a particular one. Anything further
    off than tomorrow is ``THIS_WEEK`` rather than a count of days: a number of
    days is a date, and this module holds none.
    """

    if day == today:
        return Window.TODAY
    if day == today % DAYS_IN_THE_GRID + 1:
        return Window.TOMORROW
    return Window.THIS_WEEK
