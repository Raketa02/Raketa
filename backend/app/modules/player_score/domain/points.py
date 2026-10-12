"""Player reliability in points: 100 to start, a price per failure, +5 per game
played through, six months, four bands and *New* (``docs/adr/0195`` §1, #659).

**This context keeps no record of its own.** It has no aggregate, no table and no
migration — every line it reads is folded out of ``games``' and ``bookings``'
streams at the moment somebody asks (``docs/adr/0140`` §1, which stands). A
stored figure would be a second place for *did that game happen* to be true, and
the first one to be wrong would be the copy every screen believed.

**Everyone starts at a hundred.** A failure takes a fixed price off; every game
played through gives five back; the figure never leaves 0–100. Each line drops
out **six months** after it happened, and the window rolls, so nothing ever
resets everything at once.

+----------------------------+---------------+--------+
| What happened              | Part          | Points |
+----------------------------+---------------+--------+
| Didn't come                | *Shows up*    | −25    |
| Came late                  | *Shows up*    | −10    |
| Left after the cut-off,    | *Keeps plans* | −15    |
| the seat left empty        |               |        |
| Left before the cut-off    | *Keeps plans* | −10    |
| (or a card not fixed), and |               |        |
| the empty seat called the  |               |        |
| game off                   |               |        |
| Each game played through   | —             | +5     |
+----------------------------+---------------+--------+

**The order is the lines' own moments**, because the clamp makes it matter: five
earned at a hundred is nothing, so a game played through before a miss leaves 75
and one after it leaves 80. Each line is dated **when it happened** — a game by
its booked hour, a leave by the hour or the cut-off that settled it — never by
when a fold first noticed it, so *Sergio misses Bonarka on 13 October* drops out
on 13 April.

**A *Didn't come* is priced once**, on *Shows up*: the booked game it was is
*kept* on *Keeps plans* (#659). **Silence on a score costs nothing**: *answers
about results* left the figure with the strands, and the weights went with them.
"""

from __future__ import annotations

from calendar import monthrange
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final, Iterable, Mapping, final

from app.engines.matchfit.core import ReliabilityBand, reliability_band_of
from app.kernel import Instant, instant, invariant


@final
class Happened(StrEnum):
    """One thing on a player's record that the figure or its counts read.

    **The words are this context's**, and the two providers' own — ``games``'
    turnout, ``bookings``' keeping — are mapped onto them at the seam, so the
    arithmetic below reads one vocabulary whichever context a line came from.
    """

    #: A booked game that reached its hour full with them on its court, on
    #: time, and was played — scored, disputed or *Played · no score*.
    PLAYED_THROUGH = "PLAYED_THROUGH"
    #: On time to a game that never counted, because somebody else on its
    #: court **Didn't come**: turned up, and nothing earned or lost — the game
    #: took no score, as one that started short earns those who stayed nothing.
    TURNED_UP_UNCOUNTED = "TURNED_UP_UNCOUNTED"
    #: Arrived ten to thirty minutes after the start, or said *I was there*
    #: and somebody on the court confirmed it.
    CAME_LATE = "CAME_LATE"
    #: Not at the club half an hour after the start, and no *I was there*
    #: confirmed in the day after.
    DIDNT_COME = "DIDNT_COME"
    #: Held a seat on a booked game until its hour came with every seat held.
    KEPT = "KEPT"
    #: Left after the club's cut-off and nobody took the seat, so the game went
    #: ahead short.
    LEFT_AFTER_THE_CUT_OFF = "LEFT_AFTER_THE_CUT_OFF"
    #: Left before the cut-off — or a card not fixed in time lost the seat — and
    #: the seat still empty at the cut-off called the game off for everyone.
    CALLED_OFF_BY_LEAVING = "CALLED_OFF_BY_LEAVING"
    #: Put up one of the two scores of a game left **in dispute**: information
    #: only, and it costs nothing.
    LEFT_IN_DISPUTE = "LEFT_IN_DISPUTE"


#: Where everybody starts, and the most anybody can have.
START: Final = 100

#: What each line is worth (``docs/adr/0195`` §1). **Domain, never
#: configuration**: these are what a player is told their record costs. Every
#: line has a price, nought included, so a line cannot be read without one.
PRICES: Final[Mapping[Happened, int]] = MappingProxyType(
    {
        Happened.PLAYED_THROUGH: +5,
        Happened.TURNED_UP_UNCOUNTED: 0,
        Happened.CAME_LATE: -10,
        Happened.DIDNT_COME: -25,
        Happened.KEPT: 0,
        Happened.LEFT_AFTER_THE_CUT_OFF: -15,
        Happened.CALLED_OFF_BY_LEAVING: -10,
        Happened.LEFT_IN_DISPUTE: 0,
    }
)

#: How long a line is remembered, in **calendar** months: a player told *each
#: failure drops out after six months* counts months, not days.
REMEMBERED_FOR_MONTHS: Final = 6

#: A player is **New** until this many games are played through — **ever**,
#: across sports, so six months away does not make anybody New again.
NEW_UNTIL_PLAYED_THROUGH: Final = 3


def remembered_after(now: Instant) -> Instant:
    """The moment six calendar months before ``now``: a line counts while it
    is **younger** than that, and drops out on the day it turns six months old.

    The same day of the month six months back, on the last day of a shorter
    month — so on 31 August the window opens on 28 February. Taken in UTC: the
    hour a line drops out is the hour it happened.
    """

    months = now.year * 12 + now.month - 1 - REMEMBERED_FOR_MONTHS
    year, month = divmod(months, 12)
    day = min(now.day, monthrange(year, month + 1)[1])
    return instant(now.replace(year=year, month=month + 1, day=day))


@final
@dataclass(frozen=True, slots=True)
class Line:
    """One thing that happened, and when."""

    happened: Happened
    at: Instant


@final
@dataclass(frozen=True, slots=True)
class ReliabilityCounts:
    """What the record shows beside the figure, **over the same six months**
    — counts and no ledger: the product owner chose counts over a list.

    ``turned_up`` of ``turned_up_of`` is *Shows up* — the games that reached
    their hour with them on the court, Came late counting as turned up;
    ``kept`` of ``kept_of`` is *Keeps plans* — the booked games they held a seat
    on that were settled; ``late`` is *Being late*; ``left_in_dispute`` is
    *Results left in dispute*. **Noughts are measured here**, not invented: the
    figure is points now, and *nothing in six months* is a fact a count can say.
    """

    turned_up: int
    turned_up_of: int
    late: int
    kept: int
    kept_of: int
    left_in_dispute: int

    def __post_init__(self) -> None:
        invariant(
            0 <= self.turned_up <= self.turned_up_of
            and 0 <= self.kept <= self.kept_of
            and 0 <= self.late <= self.turned_up
            and self.left_in_dispute >= 0,
            f"counts that are not counts of anything: {self}",
        )


@final
@dataclass(frozen=True, slots=True)
class PlayerScore:
    """One player's reliability: the figure, *New*, and the counts beside it.

    **Everybody has one.** A player nothing has happened to reads *100 · New*
    with every count at nought — a hundred is where everybody starts, so it is
    no longer an invented verdict about somebody nothing was arranged for.
    """

    points: int
    is_new: bool
    counts: ReliabilityCounts

    def __post_init__(self) -> None:
        invariant(
            0 <= self.points <= START,
            f"a figure that is not between nought and a hundred: {self.points}",
        )

    @property
    def band(self) -> ReliabilityBand:
        """The word under the figure — the engine's floors, never a copy."""

        return reliability_band_of(self.points)


def score_of(lines: Iterable[Line], *, now: Instant) -> PlayerScore:
    """The figure, *New* and the counts, folded from one player's record at
    ``now``. **The one fold**: every reader of a figure asks it here.

    The lines remembered — younger than six months — are taken **in time
    order** from a hundred, each clamped to 0–100; two at one moment take the
    larger cost first, so one record cannot read two figures. *New* reads every
    line, however old.
    """

    every = tuple(lines)
    since = remembered_after(now)
    remembered = sorted(
        (line for line in every if line.at > since),
        key=lambda line: (line.at, PRICES[line.happened]),
    )

    points = START
    for line in remembered:
        points = max(0, min(START, points + PRICES[line.happened]))

    seen = Counter(line.happened for line in remembered)
    turned_up = (
        seen[Happened.PLAYED_THROUGH]
        + seen[Happened.CAME_LATE]
        + seen[Happened.TURNED_UP_UNCOUNTED]
    )
    played_through_ever = sum(
        1 for line in every if line.happened is Happened.PLAYED_THROUGH
    )
    return PlayerScore(
        points=points,
        is_new=played_through_ever < NEW_UNTIL_PLAYED_THROUGH,
        counts=ReliabilityCounts(
            turned_up=turned_up,
            turned_up_of=turned_up + seen[Happened.DIDNT_COME],
            late=seen[Happened.CAME_LATE],
            kept=seen[Happened.KEPT],
            kept_of=(
                seen[Happened.KEPT]
                + seen[Happened.LEFT_AFTER_THE_CUT_OFF]
                + seen[Happened.CALLED_OFF_BY_LEAVING]
            ),
            left_in_dispute=seen[Happened.LEFT_IN_DISPUTE],
        ),
    )


__all__ = [
    "NEW_UNTIL_PLAYED_THROUGH",
    "PRICES",
    "REMEMBERED_FOR_MONTHS",
    "START",
    "Happened",
    "Line",
    "PlayerScore",
    "ReliabilityCounts",
    "remembered_after",
    "score_of",
]
