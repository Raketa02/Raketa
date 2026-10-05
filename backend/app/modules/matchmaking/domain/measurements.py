"""The curves from a measurement to a reading, on this side of the fence.

``LivenessFacts`` takes four of its ten signals as a reading in ``[0, 1]`` rather
than as the thing it measures, and its docstring says why: *a signal's points are
ruleset data; the curve from "days since they last opened the app" to a reading
is a **measurement**, and it belongs on the other side of the fence with the
clock and the ledgers.* This module is that side.

**Every curve here is linear between two named ends, and the ends are the whole
of the judgement.** A shaped curve would be a second opinion about the same fact,
invented where nothing can falsify it — the engine already prices the reading
across a bound that carries a falsifier, and a curve here would be a second
unfalsifiable number in front of it.

**A fact that is not there is ``None``, never a neutral reading.** A signal that
did not fire is absent from the offset rather than present at zero, and a ``0.5``
standing in for *we did not look* is the invented neutral this build refuses
everywhere else.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Collection, final

from app.kernel import IsoWeekday, invariant
from app.modules.player_profile.domain.weekly_hours import (
    DAYS_IN_THE_GRID,
    WeeklyHour,
)

#: Inside this many days of a session refresh, *recent activity* reads full.
#: A week, because ``last_active_at`` is projected from refresh-token events
#: against a 24-hour token lifetime and therefore **resolves days, not hours**
#: (``docs/adr/0111``) — a tighter end would be reading precision the projection
#: does not have.
ACTIVE_WITHIN_DAYS = 7

#: Past this, *dormant*. Four weeks: it is the shortest span over which *stopped
#: using the app* and *was away* are distinguishable at day resolution.
DORMANT_AFTER_DAYS = 28

#: A shared slot this far off reads as no proximity at all. The grid is an
#: ordinary week, so the whole range a shared slot can be away is 0…6 days and
#: the far end is the last of them.
PROXIMITY_HORIZON_DAYS = DAYS_IN_THE_GRID - 1

#: How many appearances still count as *barely shown*. §14.2's second rung —
#: shown once to three times lifts a little — and the rung above it is *shown
#: more often than the week's ninetieth percentile*, which is the roll's
#: published scalar rather than a number here.
BARELY_SHOWN_AT_MOST = 3

#: What *barely shown* reads. Above the midpoint, so it lifts; below the full
#: lift a player nobody has seen gets, so the two rungs stay distinguishable in
#: the recorded raw input.
BARELY_SHOWN_READING = 0.75

#: What a player inside neither rung reads. The exact midpoint, which the
#: engine's linear ramp prices at zero points and therefore drops from the
#: offset entirely — *we looked and it was ordinary* costs nobody anything.
ORDINARY_EXPOSURE_READING = 0.5


@final
@dataclass(frozen=True, slots=True)
class Overlap:
    """What two grids share, and how soon.

    ``days_away`` is ``None`` when nothing is shared, which is **not** ``0``: the
    two facts are *there is no slot* and *the slot is today*, and a day counter
    cannot say the first.
    """

    shared_count: int
    days_away: int | None

    def __post_init__(self) -> None:
        invariant(self.shared_count >= 0, f"a shared count of {self.shared_count}")
        invariant(
            self.days_away is None or 0 <= self.days_away <= PROXIMITY_HORIZON_DAYS,
            f"a shared slot {self.days_away} days away, in a seven-day week",
        )


def overlap_of(
    searcher_hours: Collection[WeeklyHour],
    candidate_slots: Collection[WeeklyHour],
    today: IsoWeekday,
) -> Overlap:
    """The cells both of them ticked, and how many days to the soonest.

    Day resolution, and the caller resolves *today* — no date and no timezone,
    the same signature ``window_of`` takes. A cell on today's weekday is nought
    days away whatever the hour is, because the grid is a preference rather than
    a promise and the product's finest time precision is a third of a day.

    It is measured here rather than read back off the engine's evidence because
    two consumers need it before any evidence exists: the recorded
    ``shared_count`` and ``days_away`` columns, and the proximity reading below.
    """

    shared = set(searcher_hours) & set(candidate_slots)
    if not shared:
        return Overlap(shared_count=0, days_away=None)
    soonest = min((int(slot.day) - int(today)) % DAYS_IN_THE_GRID for slot in shared)
    return Overlap(shared_count=len(shared), days_away=soonest)


def recent_activity_reading(
    last_active_at: datetime | None, now: datetime
) -> float | None:
    """*This week* … *dormant*, as a reading. ``None`` for a player who has never
    refreshed a session — an absence, and never a dormant player.

    Clamped at both ends rather than extrapolated: a session refreshed in the
    future is a clock skew and reads as *this week*, not as more than full.
    """

    if last_active_at is None:
        return None
    days = (now - last_active_at).total_seconds() / 86400.0
    return _ramp(days, full_at=ACTIVE_WITHIN_DAYS, empty_at=DORMANT_AFTER_DAYS)


def overlap_proximity_reading(days_away: int | None) -> float | None:
    """How soon the next slot the two of them share comes round.

    ``None`` when nothing is shared. That is the measured nothing the signal is
    entitled to be absent for — the pair has no proximity, rather than the worst
    possible proximity, and pricing it at the bottom of the ramp would charge a
    pair for a fact the availability term has already read.
    """

    if days_away is None:
        return None
    return _ramp(float(days_away), full_at=0, empty_at=PROXIMITY_HORIZON_DAYS)


def exposure_reading(times_shown: int, busy_threshold: int | None) -> float:
    """How little this candidate has been shown this week. **Three rungs.**

    §14.2's floor: shown zero times lifts, shown once to three times lifts a
    little, and shown more often than the week's ninetieth percentile docks. The
    percentile is the roll's published scalar and is ``None`` for the first hour
    of every week — in which case the top rung simply cannot be reached, which is
    the honest answer rather than a guessed threshold.

    It returns a reading rather than ``None`` because exposure is **always**
    measured: the ledger answers about every id it was asked about, zeroes
    included, and those zeroes are measured. What is not representable is *the
    store did not answer*, which fails soft to all-zeroes one layer up — safe
    here, and indefensible for a gate.
    """

    invariant(times_shown >= 0, f"a negative exposure count: {times_shown}")
    if times_shown == 0:
        return 1.0
    if busy_threshold is not None and times_shown > busy_threshold:
        return 0.0
    if times_shown <= BARELY_SHOWN_AT_MOST:
        return BARELY_SHOWN_READING
    return ORDINARY_EXPOSURE_READING


def _ramp(measured: float, *, full_at: float, empty_at: float) -> float:
    """A linear reading between two named ends, clamped outside them."""

    invariant(empty_at > full_at, f"a ramp from {full_at} to {empty_at}")
    if measured <= full_at:
        return 1.0
    if measured >= empty_at:
        return 0.0
    return 1.0 - (measured - full_at) / (empty_at - full_at)
