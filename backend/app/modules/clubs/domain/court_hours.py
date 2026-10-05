"""Where a court hour is on the clock: the club's zone, its days, and the one
conversion from a local day and hour to an instant.

**A court hour is wall clock at the club** — *Saturday 17:00 at Bonarka* — and
is stored and compared as an instant (the screens C5: *all times are stored in
UTC and shown in Europe/Warsaw*). Every day this context reasons about (an
exception's, *today*, a week's) is a local day, and every instant it hands out
is UTC.

**One zone for every club, and it is a locale assumption rather than a
constant to tune**, the shape ``plans``' ``PLATFORM_ZONE`` already takes and in
the same words: its falsifier is the first club somewhere else, and on that day
the zone becomes a fact the club records. It is spelled here rather than
imported, because a club's hours are a fact about the club and not about a
Classic play plan; a unit test holds the two spellings together.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from datetime import time as wall_time
from typing import Final

from app.kernel import (
    Instant,
    Ok,
    Zone,
    day_offset,
    instant,
    invariant,
    minute_of_day,
    slot_start,
)
from app.modules.player_profile.domain.weekly_hours import FIRST_HOUR, LAST_HOUR

#: The zone every club's hours are read in. See the module docstring.
CLUB_ZONE: Final[Zone] = Zone("Europe/Warsaw")

#: The hour a club's day of court hours opens, and the hour it closes — the
#: player's grid's own edges, 07:00 and 23:00, since no court hour exists
#: outside them. An exception or a price band covers hours between the two.
DAY_OPENS: Final = FIRST_HOUR
DAY_CLOSES: Final = LAST_HOUR + 1

_MINUTES_PER_HOUR: Final = 60

#: Local noon, which is what a date is anchored at to be converted — the one
#: wall time no zone skips or repeats (``plans``' ``_ANCHOR_WALL_TIME``).
_ANCHOR_WALL_TIME: Final = wall_time(12)


def within_the_day(opens: int, closes: int) -> bool:
    """Whether from ``opens`` until ``closes`` is at least one whole hour of a
    club's day — the one rule an exception's hours and a price band's share."""

    return DAY_OPENS <= opens < closes <= DAY_CLOSES


def local_day(at: Instant) -> date:
    """Which day it is at the club. Taking the date off the UTC instant is
    wrong for two hours of every day, in the direction nobody checks."""

    return at.astimezone(CLUB_ZONE).date()


def local_hour(at: Instant) -> int:
    """The hour of the club's wall clock ``at`` falls in."""

    return at.astimezone(CLUB_ZONE).hour


def hour_start(day: date, hour: int) -> Instant:
    """The instant the hour starting at ``hour`` on the local ``day`` begins.
    **Through ``slot_start``, and nowhere else.**

    The ``Err`` arm is unreachable for the grid and says so rather than being
    handled: a local time that does not exist in Warsaw is between 02:00 and
    03:00, and a court hour starts at seven at the earliest. Reaching it means
    the grid and the zone have stopped agreeing — the zone's falsifier arriving,
    to be found loudly.
    """

    anchor = instant(datetime.combine(day, _ANCHOR_WALL_TIME, tzinfo=CLUB_ZONE))
    converted = slot_start(
        anchor=anchor,
        day=day_offset(0),
        minute=minute_of_day(hour * _MINUTES_PER_HOUR),
        zone=CLUB_ZONE,
    )
    invariant(
        isinstance(converted, Ok),
        f"a court hour that does not exist in {CLUB_ZONE}: {day} at {hour}:00",
    )
    assert isinstance(converted, Ok)  # narrowed by the invariant above
    return converted.value


def day_closes_at(day: date) -> Instant:
    """The instant the club's ``day`` closes: the end of its last court hour,
    when every game that day is over (#548)."""

    return hour_start(day, DAY_CLOSES)


def last_closed_day(now: Instant) -> date:
    """The latest day at the clubs whose every court hour is over at ``now`` —
    today from its close on, yesterday before it (#548): the day a club is paid
    for, and the day its new bookings are summed up."""

    today = local_day(now)
    return today if now >= day_closes_at(today) else today - timedelta(days=1)
