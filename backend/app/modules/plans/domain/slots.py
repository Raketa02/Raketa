"""The three slots, what each one may hold, and the one moment they derive.

``docs/adr/0144`` fixes the order — **where · day · hour** — as *the order people
discuss them in and of decreasing negotiability*, and it is spelled once, here.

**Nothing in this file reads a clock.** A plan folds nothing against the clock
(``docs/adr/0148`` §10): a day and an hour are wall-clock facts, drawn literally
and never counted down, so every function below is a conversion or a bound and
none of them asks what time it is. The two callers that *do* need an instant —
the past-combination refusal and the horizon clamp — read one from the caller.

**One platform zone, and it is a locale assumption rather than a constant to
tune.** See ``PLATFORM_ZONE``.

**The conversion goes through ``slot_start`` and nowhere else**, so the DST
refusals the kernel already resolved are inherited rather than rewritten
(``docs/adr/0144``). That function has had no caller anywhere in ``app/`` since
it was written for the booking grid the 2026-08-25 reset deleted; a day slot and
an hour slot are precisely its two coordinates, and this is where it comes alive.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from datetime import time as wall_time
from typing import Final, final

from app.kernel import (
    Instant,
    MinuteOfDay,
    Ok,
    Zone,
    day_offset,
    instant,
    invariant,
    minute_of_day,
    slot_start,
)
from app.modules.games.domain.windows import PLAN_HORIZON
from app.modules.plans.domain.errors import (
    TheDayIsPastTheHorizon,
    TheHourIsNotOffered,
    ThePlaceIsEmpty,
    ThePlaceIsTooLong,
)

#: The one zone this platform reads a day and an hour in.
#:
#: **A locale assumption, recorded as one rather than as a constant to tune** —
#: the shape ``weekly_hours.py``'s ``_WEEKEND`` already uses. It is not a number
#: and there is nothing to try a different value of: **its falsifier is the first
#: shard whose players are somewhere else**, and on that day this becomes a fact
#: about a club or a court rather than about the platform.
#:
#: Per-device zones were refused rather than deferred (``docs/adr/0144``): they
#: would show two people on one court two different hours for one agreement, and
#: there is no club record to hold the true one.
PLATFORM_ZONE: Final[Zone] = Zone("Europe/Warsaw")

#: The longest *where* this platform stores, in characters.
#:
#: **Domain and never configuration.** It is a cap on a one-line note between the
#: people on a court, and its falsifier is the first room where somebody
#: genuinely cannot say where they are meeting in this many characters. Nothing
#: anywhere reads the value, so a longer one buys nobody anything.
PLACE_LENGTH_CAP: Final = 120

#: The step between two offered hours, in minutes.
HOUR_STEP_MINUTES: Final = 30

_MINUTES_PER_HOUR: Final = 60

#: The first hour a plan may name, as a minute of the local day. **06:00.**
EARLIEST_HOUR: Final[MinuteOfDay] = minute_of_day(6 * 60)

#: The last hour a plan may name, as a minute of the local day. **23:00.**
LATEST_HOUR: Final[MinuteOfDay] = minute_of_day(23 * 60)

#: Local noon, which is what a date is anchored at to be converted.
#:
#: **Noon rather than midnight, and the difference is a DST bug.** ``slot_start``
#: takes an *anchor* and a day offset and reads the anchor's local date; to reach
#: one particular local date the anchor has to be an instant that falls on it in
#: this zone. Midnight is the one wall time a zone is allowed to skip or repeat,
#: so anchoring there would ask the conversion a question about the very boundary
#: it exists to answer. Nothing anywhere transitions at noon.
_ANCHOR_WALL_TIME: Final = wall_time(12)


@final
@dataclass(frozen=True, slots=True)
class Place:
    """Where these people are meeting, as they wrote it down.

    **Never a court.** ``docs/adr/0144`` refuses, in writing: no id, no lookup, no
    autocomplete, no reuse, no geocode — and *nothing anywhere reads it*. It is a
    note between the people on the court and it is never a place the platform
    knows. The price is that one club will be spelled four ways and nothing will
    notice; that is what refusing a venue record costs, and it is the refusal
    that keeps *the court* out of a build with no booking, no inventory and no
    owner.

    **Validated and normalised here rather than at a caller**, on this
    repository's own rule and for ``MessageText``'s reason: this is a value a
    person composes by hand, so a bad one is a refusal with a code rather than an
    ``invariant``, and the refusal belongs to the type rather than to whichever
    route happened to receive it.
    """

    value: str

    @classmethod
    def of(cls, written: str) -> "Place":
        """Collapse it to one line, then refuse what is left if there is none.

        **One line is the shape rather than a suggestion**, so a run of
        whitespace — a newline pasted in from somewhere — becomes one space. That
        is normalisation and not a fix: the cap is then measured against what
        will actually be shown, and a chip cannot be handed a value it would draw
        as two.

        **Refused, never truncated.** A shortened *where* is one the person who
        typed it believes they wrote whole, in front of the other people on the
        court.
        """

        one_line = " ".join(written.split())
        if not one_line:
            raise ThePlaceIsEmpty()
        if len(one_line) > PLACE_LENGTH_CAP:
            raise ThePlaceIsTooLong()
        return cls(value=one_line)


def hour_of(clock_time: wall_time) -> MinuteOfDay:
    """One of the hours the platform offers, as a minute of the local day.

    **Validated server-side, and that is the point** (``docs/adr/0148`` §8). The
    client offering a grid of chips is a convention; the server refusing anything
    else is what makes ADR-0145 §9's *bounded chips the platform offered, never a
    free instant* true rather than something the next client could quietly break.

    It is a **refusal and not an ``invariant``** for ``Place``'s reason: the value
    arrives from a person tapping a chip, and a client that sent a time nobody
    offered has sent something a person could have meant.

    **Seconds are refused rather than dropped**, and they are the reason this
    takes a wall time rather than an integer. ``18:00:30`` truncated to a minute
    would be stored as ``18:00`` and read back as a value the sender never sent —
    a silent normalisation of the one field that *is* the agreement.
    """

    if clock_time.second or clock_time.microsecond:
        raise TheHourIsNotOffered()
    minute = clock_time.hour * _MINUTES_PER_HOUR + clock_time.minute
    if (
        minute < EARLIEST_HOUR
        or minute > LATEST_HOUR
        or minute % HOUR_STEP_MINUTES != 0
    ):
        raise TheHourIsNotOffered()
    return minute_of_day(minute)


def as_wall_time(minute: MinuteOfDay) -> wall_time:
    """A minute of the local day, back as a clock face.

    ``hour_of``'s inverse, and the only other place a minute and an hour meet.
    Two callers need it and they are in different layers — the wire, which sends
    a clock time, and the system line, whose value is what a room prints — so
    writing it once is what stops those two disagreeing about how 18:00 is
    spelled.
    """

    return wall_time(minute // _MINUTES_PER_HOUR, minute % _MINUTES_PER_HOUR)


def local_day(at: Instant) -> date:
    """Which day it is, on the platform's one zone. **The conversion, written once.**

    Every day this context reasons about is a **local** day — the chips a member is
    offered, the last one the horizon reaches, and *today* — while every instant it
    holds is UTC. Taking the date off an instant without converting is right for
    twenty-two hours out of twenty-four and a day out for the other two, which is
    the kind of wrong that passes every test run in the morning.

    It is here because it is the same one line as ``PLATFORM_ZONE``'s own reason:
    one zone, recorded as a locale assumption, with its falsifier named (the first
    shard whose players are somewhere else). A second spelling of it anywhere is a
    second answer to *what day is it*.
    """

    return at.astimezone(PLATFORM_ZONE).date()


def last_plannable_day(anchor: Instant) -> date:
    """The last local day a plan may name. **The clamp, and it is one line.**

    The anchor plus ``PLAN_HORIZON``, read as a local date in the platform zone,
    so a plan can never name a day past the entry window and the day row shrinks
    as the week runs out (``docs/adr/0144``). **The anchor is the challenge's
    send until the game exists, then the game's ``planned_at``**
    (``docs/adr/0164`` §4): the interlock below is defined once a game exists
    and undefined before one, and the send is the one instant a half-built court
    has. It only ever moves later, so a day chosen under the first is still
    valid under the second and the chips widen when the court fills rather than
    shrinking.

    **``PLAN_HORIZON`` stays in ``games`` and this imports it** (``docs/adr/0148``
    §8). The obvious move is to promote it to the kernel; the reason not to is
    ADR-0145 §5's interlock — the clamp and ``ENTRY_GRACE`` interlock so that
    every plannable day leaves at least twenty-four hours to say *we played* — and
    two numbers whose **relationship is the argument** must not be separated so
    that the next person to change either cannot see the other. The direction is
    the permitted one: ADR-0145's check is that ``games`` must not import the
    Plan, and this is the reverse.

    **The cost is a legitimate arrangement, and it is recorded rather than
    softened.** Two people who complete a line-up on Monday and genuinely want to
    play a fortnight out cannot say so.
    """

    return local_day(instant(anchor + PLAN_HORIZON))


def refuse_a_day_past_the_horizon(day: date, *, anchor: Instant) -> date:
    """The day, if the horizon reaches it."""

    if day > last_plannable_day(anchor):
        raise TheDayIsPastTheHorizon()
    return day


def agreed_point(*, day: date | None, hour: MinuteOfDay | None) -> Instant | None:
    """The plan's moment. **Derived, never stored, and defined whenever a day is.**

    ``docs/adr/0145`` §3, which amends ADR-0144's *day and hour both recorded*:

    - both recorded → **the agreed instant**;
    - the day alone → **the start of the following local day**;
    - no day → **nothing at all**.

    One value, coarsened rather than absent when the hour is missing — and
    coarsened **later, never earlier**, so nobody is ever asked for a result
    before they could have played. It needs no new arithmetic: the coarse case is
    the same conversion at the next day's offset and minute zero.

    **The hour alone is nothing**, and that is the rule rather than an oversight:
    an hour with no day names no moment, so a plan holding 18:00 and nothing else
    anchors as little as an empty one.
    """

    if day is None:
        return None
    if hour is not None:
        return moment_of(day, hour)
    return moment_of(day + timedelta(days=1), minute_of_day(0))


def moment_of(day: date, minute: MinuteOfDay) -> Instant:
    """The instant a local day and a local minute name, in the platform zone.
    **The only conversion here, and it goes through ``slot_start``.**

    So the autumn overlap resolves at ``fold=0`` *always, on every call* — two
    people agreeing the same slot get the same slot — and the spring-forward gap
    is refused rather than silently shifted.

    The anchor is local noon on that date, so ``slot_start``'s day offset is
    zero and the date it reads back is the one that was asked for — see
    ``_ANCHOR_WALL_TIME`` for why noon and not midnight.

    **The ``Err`` arm is unreachable and says so rather than being handled.**
    ``slot_start`` refuses a local time that does not exist, which in this zone is
    the hour between 01:59 and 03:00 on the last Sunday in March. The offered
    hours start at 06:00 and the coarse case is minute zero, so nothing this
    module can construct falls in it. It is an ``invariant`` and not a domain
    refusal because reaching it means the zone and the offered grid have stopped
    agreeing — which is ``PLATFORM_ZONE``'s falsifier arriving, and a thing to be
    found loudly rather than answered with a plausible ``None``.
    """

    anchor = instant(
        datetime.combine(day, _ANCHOR_WALL_TIME, tzinfo=PLATFORM_ZONE)
    )
    converted = slot_start(
        anchor=anchor, day=day_offset(0), minute=minute, zone=PLATFORM_ZONE
    )
    invariant(
        isinstance(converted, Ok),
        f"a plan named a local time that does not exist in {PLATFORM_ZONE}: "
        f"{day} at minute {minute}. The offered hours and the platform zone "
        f"have stopped agreeing.",
    )
    assert isinstance(converted, Ok)  # narrowed by the invariant above
    return converted.value


__all__ = [
    "EARLIEST_HOUR",
    "HOUR_STEP_MINUTES",
    "LATEST_HOUR",
    "PLACE_LENGTH_CAP",
    "PLATFORM_ZONE",
    "Place",
    "agreed_point",
    "as_wall_time",
    "hour_of",
    "last_plannable_day",
    "local_day",
    "moment_of",
    "refuse_a_day_past_the_horizon",
]
