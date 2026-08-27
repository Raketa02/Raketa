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

Which is why the floor lives in ``of_cells`` and nowhere else. **The write path
refuses; the fold accepts** — ``social_tags``' split, verbatim: ``of``, ``blank``
and ``from_codes`` must keep taking an empty grid, or a rule adopted today would
retroactively refuse to rehydrate a profile that was legal when it was written.

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

        The command path's entry point, so that a *command* carries primitives
        from the boundary and the domain is what turns them into slots
        (``backend/CONTEXT.md`` — *Command*). Raises through ``invariant`` for a
        pair that is not a cell, because the boundary schema constrains the day
        to 1–7 and the part to the three there are: reaching this with anything
        else means a caller inside the application built it.

        **This is the one place the floor is enforced**, because it is the one
        place a player's own answer arrives. Nothing ticked is refused with
        ``AvailabilityGridEmpty`` — a *refusal* rather than a broken
        precondition, because it is a legitimate thing for a client to send and
        the client's recovery is to go back to the week and tick a cell.

        Counted **after** the fold, so a client that sent Tuesday morning three
        times is at one and not at three: the count is of cells, which is what
        the player ticked, and never of what arrived.
        """

        grid = cls.of(
            AvailabilitySlot(day=iso_weekday(day), part=_part(part))
            for day, part in cells
        )
        if not grid.slots:
            raise AvailabilityGridEmpty()
        return grid

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
