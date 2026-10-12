"""Who turned up to a booked game, caught at the court while it happens (#657;
``docs/adr/0195`` §3, the mechanics §15.1).

**Only a real absence starts anything.** Everybody who arrives on time does
nothing at all: nothing is recorded about a player nobody tapped. A player on
the court taps *Oscar isn't here yet* in the **tap window** — the first half of
the game — and Oscar's **arrival** is the first *I'm here* or *they're here*
after it. The arrival's moment decides what it was: **on time** within ten
minutes of the start (nothing is recorded, and the tap vanishes), **Came late**
up to thirty, and **Didn't come** with no arrival by then. A phone that died
has one way back: *I was there* within a day of the tap window closing,
confirmed by somebody else on the court, turns *Didn't come* into *Came late* —
the tap still proves they were not there when it was made.

**Folded per player, against the server's clock** and never the phone's —
``state_of`` is the one place an outcome is read, and nothing stores one.

**Every tap made in the window is checked at the club, and the Game is handed
only the verdict.** The phone sends a one-shot fix with the tap; the application
layer measures it against the booking's club map point (``GameClubs``) and hands
the Game a ``ClubVerdict``. **The coordinates are never stored**: not on an
event, not in a log, not in a table — an event a tap writes is itself the record
that its maker was at the club then, since a tap from anywhere else is refused
and writes nothing. The late claim and its confirmation are made a day later,
from wherever the player is, and carry no fix: what proves them is somebody else
on the court (a call made beside ``docs/adr/0195`` §3, #657).

**None of the numbers here is configuration** (``windows.py``'s rule): they are
what a player is promised.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Final, final
from uuid import UUID

from app.kernel import Instant
from app.modules.games.domain.errors import ALocationFixIsOffTheMap
from app.modules.games.domain.windows import (
    late_claim_closes_at,
    on_time_until,
    tap_window_closes_at,
)

#: **At the club** is within this many metres of the club's map point (a call,
#: ``docs/adr/0195`` §10.2).
AT_THE_CLUB_WITHIN_M: Final = 300.0

#: How much of a fix's own stated accuracy is allowed for, at most — so that a
#: large indoor hall, where a phone's fix wanders, still passes. A fix that says
#: it could be a kilometre out is given this much and no more.
ACCURACY_ALLOWED_UP_TO_M: Final = 200.0


@final
@dataclass(frozen=True, slots=True)
class LocationFix:
    """One precise fix a phone read at the moment of an attendance tap. **Held
    for the length of the request and never stored** — not on an event, not in
    a log line, not in a table.

    ``accuracy_m`` is the fix's own stated accuracy: the radius the phone says
    the true position lies within.
    """

    latitude: float
    longitude: float
    accuracy_m: float

    def __post_init__(self) -> None:
        # **A refusal, never an invariant**: a fix arrives from a phone, as a
        # club's point arrives from its desk (``clubs``' ``MapPoint``).
        if not (
            math.isfinite(self.latitude)
            and -90.0 <= self.latitude <= 90.0
            and math.isfinite(self.longitude)
            and -180.0 <= self.longitude <= 180.0
            and math.isfinite(self.accuracy_m)
            and self.accuracy_m >= 0.0
        ):
            raise ALocationFixIsOffTheMap()

    def __repr__(self) -> str:
        # A fix that reached a log through a repr would be a stored position.
        return "LocationFix(<withheld>)"


@final
@dataclass(frozen=True, slots=True)
class ClubVerdict:
    """**At the club, at that time** — the one thing an attendance tap hands
    the Game about where its maker is. ``club_name`` is what the refusal says
    (*You can say so only from Ogrody 33*), and ``None`` for a booking whose
    club could not be read, which is never at the club."""

    at_the_club: bool
    club_name: str | None

    @classmethod
    def of(
        cls, *, metres: float | None, accuracy_m: float, club_name: str | None
    ) -> "ClubVerdict":
        """Within ``AT_THE_CLUB_WITHIN_M`` of the club's point, allowing for the
        fix's own accuracy up to ``ACCURACY_ALLOWED_UP_TO_M``. ``metres`` is
        ``None`` when the club's point could not be read."""

        if metres is None:
            return cls(at_the_club=False, club_name=club_name)
        allowed = min(accuracy_m, ACCURACY_ALLOWED_UP_TO_M)
        return cls(
            at_the_club=metres - allowed <= AT_THE_CLUB_WITHIN_M,
            club_name=club_name,
        )


@final
class AttendanceState(str, Enum):
    """What became of one player somebody said was not here yet."""

    #: Tapped, not arrived, and the tap window still runs.
    WAITING = "WAITING"
    #: Arrived within ten minutes of the start: nothing is recorded.
    ON_TIME = "ON_TIME"
    #: Arrived ten to thirty minutes after the start.
    CAME_LATE = "CAME_LATE"
    #: No arrival by the tap window's end, and no *I was there* waiting —
    #: provisional until the late claim's day ends, then final.
    DIDNT_COME = "DIDNT_COME"
    #: Said *I was there*, and nobody has confirmed it yet; the late claim's
    #: day still runs. Until a confirmation, it is still *Didn't come*.
    CLAIMED = "CLAIMED"
    #: *I was there*, confirmed by somebody else on the court: **Came late**.
    CONFIRMED = "CONFIRMED"


#: The states whose outcome is **Didn't come** — the game takes no score and
#: never counts while any player on it is in one.
DIDNT_COME_STATES: Final = frozenset(
    {AttendanceState.DIDNT_COME, AttendanceState.CLAIMED}
)

#: The states of a player who is **not here** — awaited, or Didn't come — who
#: may not say who else is here, nor vouch for anybody.
NOT_HERE_STATES: Final = DIDNT_COME_STATES | {AttendanceState.WAITING}

#: The states whose outcome is **Came late**.
CAME_LATE_STATES: Final = frozenset(
    {AttendanceState.CAME_LATE, AttendanceState.CONFIRMED}
)


@final
@dataclass(frozen=True, slots=True)
class Absence:
    """One player somebody on the court said was not here yet, and what has
    been said since — folded off the game's four attendance events."""

    #: Who first said so, and when. A second *isn't here yet* writes nothing.
    noted_by: UUID
    noted_at: Instant
    #: The first *I'm here* or *they're here* — **the arrival** — and who made it.
    arrived_at: Instant | None = None
    arrival_noted_by: UUID | None = None
    #: *I was there*, a day later at most.
    claimed_at: Instant | None = None
    #: *Yes, they were here*, from somebody else on the court.
    confirmed_at: Instant | None = None
    confirmed_by: UUID | None = None


def state_of(absence: Absence, *, starts_at: Instant, now: Instant) -> AttendanceState:
    """What this absence is at ``now``. **The one fold**: every reader of an
    outcome — the standing, the wire, the record — asks it here.

    The arrival decides first, because once somebody arrived nothing later can
    change when. Then a confirmed claim, which is final. Then the clock: inside
    the tap window the player is still awaited; after it, a claim still inside
    its day waits on a confirmation, and everything else is *Didn't come*.
    """

    if absence.arrived_at is not None:
        if absence.arrived_at < on_time_until(starts_at):
            return AttendanceState.ON_TIME
        return AttendanceState.CAME_LATE
    if absence.confirmed_at is not None:
        return AttendanceState.CONFIRMED
    if now < tap_window_closes_at(starts_at):
        return AttendanceState.WAITING
    if absence.claimed_at is not None and now < late_claim_closes_at(starts_at):
        return AttendanceState.CLAIMED
    return AttendanceState.DIDNT_COME


def is_final(state: AttendanceState, *, starts_at: Instant, now: Instant) -> bool:
    """Whether nothing more can change this outcome at ``now``: an arrival, a
    confirmation, or a *Didn't come* whose late claim's day is over."""

    if state in (AttendanceState.WAITING, AttendanceState.CLAIMED):
        return False
    if state is AttendanceState.DIDNT_COME:
        return now >= late_claim_closes_at(starts_at)
    return True


__all__ = [
    "ACCURACY_ALLOWED_UP_TO_M",
    "AT_THE_CLUB_WITHIN_M",
    "Absence",
    "AttendanceState",
    "CAME_LATE_STATES",
    "ClubVerdict",
    "DIDNT_COME_STATES",
    "LocationFix",
    "NOT_HERE_STATES",
    "is_final",
    "state_of",
]
