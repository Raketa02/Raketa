"""Time: instants, the integer coordinates engines compute in, and the one
conversion between them.

See ``docs/adr/0024-instant-as-aware-datetime-minute-coordinates.md``.

**An ``Instant`` is a timezone-aware ``datetime`` in UTC.** Not epoch
milliseconds — the source specification documents say otherwise, at length, and
their argument is against JavaScript's ``Date``, none of which is true of
Python's ``datetime``. This repository already has exactly one time
representation: the clock returns an aware ``datetime``, every domain event
carries one, and Postgres stores ``timestamptz``. A second one would buy a
conversion at four boundaries and nothing else.

``Instant`` is a ``NewType``, so it is a *refinement* of the aware ``datetime``
those modules already pass around: an ``Instant`` goes wherever a ``datetime``
is wanted, and a bare ``datetime`` does not go where an ``Instant`` is required.
That asymmetry is the whole of the brand, and it is why adopting it is an import
change rather than a rewrite.

**Booking arithmetic happens in integers.** ``MinuteOfDay``, ``DayOffset`` and
``Minutes`` are branded ``int``s, and engines compute in them, because that is
what makes an availability check a handful of integer comparisons rather than
datetime arithmetic. The hot path never touches an ``Instant``.

**There is exactly one conversion from coordinates to an instant** —
``slot_start``. Nothing else constructs an instant from a day and a minute, so
every timezone question in the system has one place to be asked and one place
to be tested. ``zoneinfo`` is imported here and nowhere else in ``app/``, which
``tests/unit/test_kernel_time.py`` walks the tree to check.

**DST is handled explicitly, not hoped over.** Poland observes it: a day in
March has twenty-three hours, a day in October has twenty-five, and one local
hour occurs twice. Each of the three behaviours is written out at its call site
below, because each is silent when it is wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from datetime import time as wall_time
from typing import Literal, NewType, Protocol, TypeAlias, runtime_checkable
from zoneinfo import ZoneInfo

from app.kernel.invariants import invariant
from app.kernel.results import Err, Ok, Result

#: Minutes in a *nominal* day, which is the coordinate space — not the length of
#: any particular local day. Two days a year in Warsaw run 1380 and 1500 real
#: minutes, and that difference is `slot_start`'s business, not a coordinate's.
MINUTES_PER_DAY = 1440

_MINUTES_PER_HOUR = 60
_SECONDS_PER_MINUTE = 60

#: A moment in time: a timezone-aware `datetime` normalised to UTC.
Instant = NewType("Instant", datetime)

#: Minutes since local midnight, `0 <= value < MINUTES_PER_DAY`.
MinuteOfDay = NewType("MinuteOfDay", int)

#: Whole calendar days from an anchor's *local* date. **In-memory only** — see
#: `day_offset`.
DayOffset = NewType("DayOffset", int)

#: A length of time in whole minutes. Signed: negative runs backwards.
Minutes = NewType("Minutes", int)

#: A length of time in whole seconds. Signed, like `Minutes`, and **a separate
#: brand rather than a finer spelling of it**: the two are not interchangeable,
#: and a `Minutes` handed to something expecting a `Seconds` is a sixtyfold
#: error that reads perfectly.
#:
#: It exists because one rule in the system is measured below a minute — a seat
#: claim's thirty-second cooldown
#: (``docs/adr/0081-a-seat-is-never-taken-until-it-is-paid.md``),
#: which is *"enough to break a tap-loop, not enough to cost a mistyped PIN a
#: Saturday game."* Rounding it up to a minute would be that rule told as a lie,
#: and writing it as a bare `timedelta` at its call site would reach past the
#: validating constructor, which is exactly what a brand is for.
Seconds = NewType("Seconds", int)

#: A day of the local week, ISO-numbered: Monday 1 through Sunday 7.
IsoWeekday = NewType("IsoWeekday", int)

#: An IANA timezone. Exported so that a caller may *hold* a zone — a club's, say —
#: without importing `zoneinfo`, which this module does exactly once for the whole
#: of `app/` and which a walk keeps that way. Naming it here is what makes the
#: rule enforceable rather than aspirational: the type is available everywhere,
#: and the answers derived from it are still only available from this file.
Zone: TypeAlias = ZoneInfo


def _not_a_bool(value: int, named: str) -> int:
    """Refuse the one `int` that is never a coordinate.

    `bool` is a subclass of `int`, so `minute_of_day(True)` typechecks and means
    *one minute past midnight* — a wrong answer rather than a loud one, and the
    only value in the type that is always a mistake.
    """

    invariant(not isinstance(value, bool), f"{named} from a bool: {value!r}")
    return value


def instant(value: datetime) -> Instant:
    """Normalise an aware ``datetime`` to UTC, or raise because it is naive.

    A naive datetime is the classic bug this type exists to make unwritable: it
    reads as a time and behaves as one right up to the point where two of them
    are compared, and then it is a `TypeError` in production or, worse, a
    silent hour.

    Both halves of the check are load-bearing. `tzinfo is not None` is not
    enough on its own — the standard library's definition of *aware* is that
    `utcoffset()` returns an offset, and a `tzinfo` that returns `None` is a
    naive datetime wearing a hat.

    An aware value in some other zone is the same instant, so it is converted
    rather than refused: UTC is the canonical spelling, not an extra demand.
    """

    invariant(
        value.tzinfo is not None and value.utcoffset() is not None,
        f"instant from a naive datetime: {value!r}",
    )
    return Instant(value.astimezone(timezone.utc))


def minute_of_day(value: int) -> MinuteOfDay:
    """Minutes since local midnight. Outside the day is a bug, so it raises."""

    invariant(0 <= value < MINUTES_PER_DAY, f"minute of day: {value}")
    return MinuteOfDay(_not_a_bool(value, "minute of day"))


def day_offset(value: int) -> DayOffset:
    """Whole calendar days from an anchor's local date.

    **Negative is legal**: history is yesterday, and a grid that can only look
    forwards cannot show a club what happened last week.

    **Never persisted and never serialised.** A `DayOffset` means nothing
    without the anchor it was computed against, so a stored or wire-borne one is
    a number that silently changes meaning the next time it is read. It is an
    in-memory coordinate, and the moment a day has to leave the process it
    leaves as an `Instant` or as a local `date`.
    """

    return DayOffset(_not_a_bool(value, "day offset"))


def iso_weekday(value: int) -> IsoWeekday:
    """A day of the week as ISO 8601 numbers one: Monday 1 through Sunday 7.

    Branded for the same reason `MinuteOfDay` is, and against the same mistake:
    an unbranded weekday is an `int`, and `minute_of_day(3)` is a perfectly
    legal minute meaning *three minutes past midnight*. Wednesday read as
    00:03 is a wrong answer rather than a loud one, and the two quantities meet
    in every module that compares a start against a declared window.

    **ISO numbering, and no start of the week.** Which day a week *begins* on
    is a constant with no owner (`docs/adr/0024`) and nothing here needs one:
    membership of a set of days is the only question asked of this, and a set
    has no first element.
    """

    invariant(1 <= value <= 7, f"iso weekday: {value}")
    return IsoWeekday(_not_a_bool(value, "iso weekday"))


def minutes(value: int) -> Minutes:
    """A length of time in whole minutes; negative runs backwards."""

    return Minutes(_not_a_bool(value, "minutes"))


def hours(count: int) -> Minutes:
    """A length of time in whole hours, as minutes.

    Here so that a twelve-hour rule is written `hours(12)` once rather than
    `Minutes(12 * 60)` at each call site — the second spelling reaches past the
    validating constructor, which is exactly what a brand is for.
    """

    return minutes(_not_a_bool(count, "hours") * _MINUTES_PER_HOUR)


def seconds(value: int) -> Seconds:
    """A length of time in whole seconds; negative runs backwards."""

    return Seconds(_not_a_bool(value, "seconds"))


@dataclass(frozen=True)
class NonexistentLocalTime:
    """That local time does not exist on that date, in that zone.

    The spring-forward gap: Warsaw's clocks go 01:59 → 03:00 on the last Sunday
    in March, so nothing on that date is 02:30. Returned rather than raised,
    because a booking grid asking for every half hour of that day is asking a
    perfectly reasonable question — the answer for that one hour is *there are
    no minutes here*, and the caller draws the gap.

    Payload, not prose (`Reason`): the client owns the words. `local_date`
    rather than the day offset it was asked as, because a `DayOffset` is
    anchor-relative and must not leave the process.
    """

    zone: str
    local_date: date
    minute_of_day: MinuteOfDay
    kind: Literal["nonexistent_local_time"] = "nonexistent_local_time"


def slot_start(
    *,
    anchor: Instant,
    day: DayOffset,
    minute: MinuteOfDay,
    zone: Zone,
) -> Result[Instant, NonexistentLocalTime]:
    """The single conversion from in-day coordinates to an instant.

    Day zero is the anchor's **local** calendar date in `zone`, which is not
    always its UTC date — 23:00 UTC on a Saturday is already Sunday in Warsaw,
    and a grid anchored there must show Sunday.
    """

    local_date = anchor.astimezone(zone).date() + timedelta(days=day)
    wall = datetime.combine(
        local_date,
        wall_time(minute // _MINUTES_PER_HOUR, minute % _MINUTES_PER_HOUR),
    )

    # `fold=0` is the ambiguous-time decision, written out rather than inherited
    # from the default that happens to agree with it. On the autumn overlap
    # 02:30 happens twice, and this always resolves to the **earlier** offset —
    # always, on every call, so two people booking the same slot get the same
    # slot. A rule left to a default is a rule a refactor can change silently.
    local = wall.replace(tzinfo=zone, fold=0)

    # The round-trip idiom, and the reason this function is not three lines.
    # **Python does not raise for a local time that does not exist.** It hands
    # back a value computed with the pre-transition offset, and that value looks
    # entirely ordinary. So: convert to UTC and back, and compare the **wall
    # clock**. A nonexistent time returns with a different clock face at the
    # *same instant* — 02:30+01:00 comes back as 03:30+02:00 — so comparing the
    # two UTC forms compares equal and detects nothing at all. That is the
    # simplification to refuse; `wall` is naive here so the comparison cannot
    # quietly become one.
    #
    # (Comparing the two *aware* values happens to work, because PEP 495 makes a
    # same-zone comparison a naive one. It is the same check resting on a rule
    # nobody reads, and one `astimezone` away from the version that is wrong.)
    #
    # Delete this and the booking grid offers an hour that has no minutes in it.
    if local.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != wall:
        return Err(
            NonexistentLocalTime(
                zone=zone.key or str(zone),
                local_date=local_date,
                minute_of_day=minute,
            )
        )

    return Ok(instant(local))


def local_minute_of_day(moment: Instant, zone: Zone) -> MinuteOfDay:
    """Read an instant back as a minute of its local day — `slot_start`'s
    inverse for the minute, and the half that makes the round trip testable."""

    local = moment.astimezone(zone)
    return minute_of_day(local.hour * _MINUTES_PER_HOUR + local.minute)


def local_iso_weekday(moment: Instant, zone: Zone) -> IsoWeekday:
    """Which day of the local week an instant falls on. The other half of the read.

    Beside `local_minute_of_day` because they are one question asked twice — *what
    does the clock on that wall say* — and because a caller comparing a start
    against a declared *Tuesday evening* needs both halves to have come from the
    same zone. Asking either of them by hand is the mistake: 22:30 UTC on a Sunday
    is already Monday in Warsaw, so a weekday read off the instant's own date is
    wrong for two hours of every day and wrong in the direction nobody checks.
    """

    return iso_weekday(moment.astimezone(zone).isoweekday())


def elapsed_minutes(start: Instant, end: Instant) -> Minutes:
    """Whole minutes that **elapse** from `start` to `end`, floored.

    Elapsed, never wall-clock subtraction. A twelve-hour rule means twelve
    elapsed hours, and computing it by subtracting from a wall-clock hour is
    wrong twice a year — the failure binds four people who have already paid to
    a match an hour early or late. Both arguments are UTC instants, so there is
    no wall clock here to subtract from and the mistake has nowhere to live.

    Floored rather than truncated toward zero, so it is monotonic in `end` and
    has no flat spot straddling zero. `timedelta` normalises with `days`
    carrying the sign and `seconds` non-negative, so the integer arithmetic
    below *is* the floor, exactly, with no float in it.
    """

    delta = end - start
    return minutes(delta.days * MINUTES_PER_DAY + delta.seconds // _MINUTES_PER_HOUR)


def moved(moment: Instant, by: Seconds) -> Instant:
    """`moment` moved by `by` **elapsed** seconds; negative moves backwards.

    **The one place an instant is moved at all**, with `shifted` as its wrapper
    rather than the other way round — the same relationship `court_named_at` has
    to `door_code_at`, and for the same reason. Minutes are the currency of
    almost every rule in the system, so `shifted` is what nearly every caller
    wants; but a rule measured in seconds cannot be spelled in minutes at all,
    and two constructions of a `timedelta` would be two places for the
    elapsed-versus-wall-clock question to be answered.
    """

    return instant(moment + timedelta(seconds=by))


def shifted(moment: Instant, by: Minutes) -> Instant:
    """`moment` moved by `by` **elapsed** minutes; negative moves backwards.

    A ninety-minute slot sold across a spring-forward keeps its ninety minutes
    and its wall-clock end time moves, which is what the players agreed to: the
    court is booked for an hour and a half, not until a particular clock face.
    """

    return moved(moment, seconds(by * _SECONDS_PER_MINUTE))


@runtime_checkable
class Clock(Protocol):
    """The one way any code learns what time it is.

    **Passed, never imported.** No module reads ambient time: that is
    ADR-0015's first purity rule, and it is what makes the system reproducible —
    scrubbing a clock forwards and backwards, determinism, and every test that
    depends on a fixed now. The interface is born here, in the kernel, so that
    depending on *what a clock is* does not drag a live one into scope; its
    wall-clock adapter belongs in the infrastructure layer.

    One read per command, captured once and passed to every engine that command
    calls. Two reads inside one command can disagree.
    """

    def now(self) -> Instant: ...
