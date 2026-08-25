"""Deliberately-wrong uses of the pure layer, each one a constraint being claimed.

Named for the kernel, and the kernel is all it covers: one subject file, so one
``mypy`` run answers for the whole fence rather than one per package.

This file is **not run and not collected**. It is read by ``mypy``, driven from
``tests/unit/test_kernel_typing.py``, which asserts that every line marked with
a ``# want-error:`` comment produces exactly that error code — and that no line
without one produces any error at all.

Why it exists: the kernel's constraints are carried by the type system, and the
type system erases at runtime. Delete ``@final`` from ``Ok``, widen ``Err``'s
reason to ``object``, drop the ``Never`` from ``exhaustive`` — every one of those
changes behaviour not at all, breaks no test, and passes review as a
simplification. The claim *"a minute is not a weekday"* is worth precisely what
checks it.

**Adding a case is the point.** Each branded module lands its own misuses here,
and the time module's coordinates are the ones below — a `MinuteOfDay` passed
where an `IsoWeekday` belongs is a claim about the compiler and nothing else
could check it.

Every legitimate use below is load-bearing too: it is a line the harness asserts
is *clean*, so a constraint that grows teeth it should not have — a narrowing
that stops narrowing, a chain that stops composing — fails here as loudly as one
that loses them.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from app.kernel import (
    SPORT_SPECS,
    Clock,
    DayOffset,
    Err,
    Instant,
    InvariantViolated,
    IsoWeekday,
    MinuteOfDay,
    Minutes,
    NonexistentLocalTime,
    Ok,
    Reason,
    Result,
    Sport,
    SportSpec,
    Unavailable,
    Zone,
    day_offset,
    elapsed_minutes,
    exhaustive,
    hours,
    instant,
    invariant,
    iso_weekday,
    local_iso_weekday,
    local_minute_of_day,
    minute_of_day,
    minutes,
    shifted,
    slot_start,
)


@dataclass(frozen=True)
class Closed:
    """A stand-in reason: a machine code and its payload, no sentence."""

    day_offset: int
    kind: Literal["closed"] = "closed"


@dataclass(frozen=True)
class Sentenced:
    """A stand-in for the reason nobody may write: words instead of a code."""

    message: str


# --- Result has exactly two inhabitants, and neither is open -------------------


class ThirdInhabitant(Ok[int]):  # want-error: misc
    """A success that is also something else. `@final` is what forbids it."""


class FourthInhabitant(Err[Closed]):  # want-error: misc
    """Likewise a failure. Two `@final` classes are the whole closed set."""


def a_result_is_immutable(result: Ok[int]) -> None:
    result.value = 2  # want-error: misc


def both_members_must_be_handled(result: Result[int, Closed]) -> int:
    """A match that handles only the success is not a match over a `Result`."""

    match result:
        case Ok(value):
            return value
        case _:
            exhaustive(result)  # want-error: arg-type


# --- A reason is a machine code, never a sentence ------------------------------

#: The case that catches the `Reason` bound being widened, and the only one that
#: does. With no annotation to solve `_R` from, the bound is the sole thing that
#: can refuse this. The two functions below are refused by their *return type*
#: as well, so both would survive `_R` losing its bound entirely — which is what
#: a mutation run found, and why this line is here.
A_SENTENCE_IS_NOT_A_REASON = Err("No courts are available.")  # want-error: type-var


def a_reason_is_never_a_sentence() -> Err[Reason]:
    """The whole point of the `Reason` bound, and the one a reviewer forgets."""

    return Err("No courts are available that afternoon.")  # want-error: arg-type


def a_reason_without_a_code_is_not_a_reason() -> Err[Reason]:
    """`Sentenced` carries words and no `kind`, so it is not a reason at all."""

    return Err(Sentenced(message="No courts available."))  # want-error: arg-type


def a_reason_is_a_plain_frozen_dataclass() -> Err[Closed]:
    """And this one is clean: declaring `kind` is the whole of the contract."""

    return Err(Closed(day_offset=1))


# --- The reason union is closed, and the compiler knows what is in it ---------


def a_reason_nobody_declared_is_not_unavailable() -> Result[int, Unavailable]:
    """`Closed` is a stand-in defined in this file, so it is not in the union.

    This is what makes *"the closed set of reasons the kernel can give"* a fact
    rather than a comment: a module cannot widen it by declaring a dataclass,
    only by adding a line to `app/kernel/unavailability.py`.

    It was `return-value` while the union was `Never` and became `arg-type` when
    it gained a member — with something concrete to solve `_R` against, mypy
    refuses the reason rather than the return. Same constraint, and the marker
    tracks what the compiler actually says.
    """

    return Err(Closed(day_offset=1))  # want-error: arg-type


def the_union_has_a_member_now() -> Result[int, Unavailable]:
    """It shipped as `Never`. The time module landed the first real reason."""

    return Err(
        NonexistentLocalTime(
            zone="Europe/Warsaw",
            local_date=date(2026, 3, 29),
            minute_of_day=minute_of_day(150),
        )
    )


def a_result_that_cannot_fail_is_still_a_result() -> Result[int, Unavailable]:
    return Ok(1)


# --- Mapping and chaining keep the reason's type ------------------------------


@dataclass(frozen=True)
class Elsewhere:
    kind: Literal["elsewhere"] = "elsewhere"


def a_chain_cannot_swap_the_reason(
    result: Result[int, Closed],
) -> Result[str, Closed]:
    """`and_then` composes only where the two halves can fail the same way."""

    return result.and_then(lambda value: Err(Elsewhere()))  # want-error: arg-type


def a_chain_composes(result: Result[int, Closed]) -> Result[str, Closed]:
    return result.and_then(lambda value: Ok(str(value)))


def a_map_keeps_the_reason(result: Result[int, Closed]) -> Result[str, Closed]:
    return result.map(str)


# --- `invariant` narrows, and the narrowing is the reason it is not an `if` ---


def without_the_invariant(sport: Sport) -> int:
    """The state a caller is in before the guard: the lookup may miss."""

    spec = SPORT_SPECS.get(sport)
    return spec.players  # want-error: union-attr


def with_the_invariant(sport: Sport) -> int:
    """And after it. This line erroring means the narrowing has stopped.

    It is the half of the pair that cannot be asserted by marking it — an
    absence of an error is only evidence when something otherwise identical
    does produce one, which is what the function above is for.
    """

    spec: SportSpec = invariant(SPORT_SPECS.get(sport), f"no spec: {sport!r}")
    return spec.players


def an_invariant_is_not_caught_as_a_value_error() -> None:
    """`InvariantViolated` is deliberately not a `ValueError`."""

    try:
        invariant(None, "nothing")
    except InvariantViolated:
        pass


# --- Exhaustiveness over the registry that is already closed ------------------


def every_sport_must_be_named(sport: Sport) -> str:
    """Badminton is missing, so `sport` is not `Never` where the tail sits."""

    match sport:
        case Sport.PADEL:
            return "padel"
        case Sport.TENNIS:
            return "tennis"
        case Sport.SQUASH:
            return "squash"
        case _:
            exhaustive(sport)  # want-error: arg-type


def all_four_named(sport: Sport) -> str:
    match sport:
        case Sport.PADEL:
            return "padel"
        case Sport.TENNIS:
            return "tennis"
        case Sport.SQUASH:
            return "squash"
        case Sport.BADMINTON:
            return "badminton"
        case _:
            exhaustive(sport)


# --- Time: the brands bind, and a coordinate is not another coordinate --------
#
# `Instant`, `MinuteOfDay`, `DayOffset` and `Minutes` are `NewType`s, which erase
# to `datetime` and `int` at runtime. Collapse them to their base types and every
# test in the suite still passes — these lines are the only thing that notices.

WARSAW = ZoneInfo("Europe/Warsaw")
NOON = instant(datetime(2026, 3, 29, 12, 0, tzinfo=timezone.utc))


def a_raw_minute_is_not_a_minute_of_day() -> Result[Instant, NonexistentLocalTime]:
    """The brand's whole job: an unvalidated integer cannot reach the grid."""

    return slot_start(
        anchor=NOON,
        day=day_offset(0),
        minute=150,  # want-error: arg-type
        zone=WARSAW,
    )


def a_day_is_not_a_minute() -> Result[Instant, NonexistentLocalTime]:
    """Two `NewType`s over `int`, and they do not interchange — transposing
    them asks for day 150 of a grid, silently and with no wrong-looking value
    anywhere in the call."""

    return slot_start(
        anchor=NOON,
        day=day_offset(0),
        minute=day_offset(150),  # want-error: arg-type
        zone=WARSAW,
    )


def a_minute_is_not_a_day() -> Result[Instant, NonexistentLocalTime]:
    """And the same claim from the other side, which is the load-bearing half.

    A mutation run found this missing. Every case above is refused by
    `MinuteOfDay`'s brand, so **dropping `DayOffset`'s left the suite green** —
    `day_offset(150)` returning a plain `int` is still refused where a
    `MinuteOfDay` is wanted. Only a case refused by `DayOffset` *itself* catches
    that, and this and the next one are those: with `DayOffset = int`, a
    `MinuteOfDay` and a literal both become assignable and both lines go clean.
    """

    return slot_start(
        anchor=NOON,
        day=minute_of_day(0),  # want-error: arg-type
        minute=minute_of_day(150),
        zone=WARSAW,
    )


def a_raw_day_is_not_a_day_offset() -> Result[Instant, NonexistentLocalTime]:
    return slot_start(
        anchor=NOON,
        day=0,  # want-error: arg-type
        minute=minute_of_day(150),
        zone=WARSAW,
    )


def a_duration_is_not_a_minute_of_day() -> Result[Instant, NonexistentLocalTime]:
    """A length of time and a point in the day are both minutes, and neither
    is the other — a ninety-minute slot is not 01:30."""

    return slot_start(
        anchor=NOON,
        day=day_offset(0),
        minute=minutes(90),  # want-error: arg-type
        zone=WARSAW,
    )


def a_plain_datetime_is_not_an_instant() -> Minutes:
    """Which is what makes `instant()` the one way in, naive check included."""

    return elapsed_minutes(datetime(2026, 3, 29, 10, 0), NOON)  # want-error: arg-type


def an_aware_datetime_is_not_an_instant_either() -> Minutes:
    """Aware is *necessary*, not sufficient: an `Instant` is aware **and** UTC,
    and only the constructor establishes that."""

    aware = datetime(2026, 3, 29, 10, 0, tzinfo=timezone.utc)
    return elapsed_minutes(aware, NOON)  # want-error: arg-type


def a_duration_is_not_a_number_of_minutes_either() -> Instant:
    return shifted(NOON, 90)  # want-error: arg-type


# --- And the refinement holds in the direction #75 depends on -----------------


def an_instant_goes_wherever_a_datetime_is_wanted(moment: Instant) -> datetime:
    """The claim that made retiring `app/shared/clock.py` (#75) an import change
    rather than a rewrite: every existing signature already takes this."""

    return moment


def a_minute_of_day_is_still_an_int(minute: MinuteOfDay) -> int:
    return minute * 2


def a_clock_returns_an_instant(clock: Clock) -> datetime:
    return clock.now()


def a_weekday_is_not_a_minute_of_day() -> MinuteOfDay:
    """The case `IsoWeekday`'s brand alone catches, and the reason it exists.

    Both are `NewType`s over `int` and Wednesday is 3, which is also a perfectly
    legal minute meaning *three minutes past midnight*. Collapse `IsoWeekday` to
    `int` and this line goes quiet while every runtime test still passes.
    """

    return local_iso_weekday(NOON, WARSAW)  # want-error: return-value


def a_weekday_is_not_a_day_offset() -> DayOffset:
    """Anchor-relative days and days of the week are different quantities.

    Sunday is 7 and *seven days from the anchor* is 7, so the transposition has no
    wrong-looking value anywhere in it — the two brands are the only thing between
    a card offered next Sunday and one offered a week today.
    """

    return iso_weekday(7)  # want-error: return-value


def a_minute_is_not_a_weekday() -> IsoWeekday:
    """And the other direction, which the range check cannot make loud.

    `iso_weekday` refuses anything outside 1..7 at runtime, so a minute of 600
    raises — but a minute of 3 does not, and that is the call this line refuses
    before it can be written.
    """

    return local_minute_of_day(NOON, WARSAW)  # want-error: return-value


def a_zone_is_what_both_readers_take() -> tuple[IsoWeekday, MinuteOfDay]:
    """The legitimate use beside them: one instant, one zone, both halves."""

    return local_iso_weekday(NOON, WARSAW), local_minute_of_day(NOON, WARSAW)


def a_zone_may_be_held_without_importing_zoneinfo(zone: Zone) -> IsoWeekday:
    """And the reason `Zone` is exported at all: an engine names the type."""

    return local_iso_weekday(NOON, zone)


def the_coordinates_compose(anchor: Instant) -> Result[Instant, NonexistentLocalTime]:
    return slot_start(
        anchor=shifted(anchor, hours(-12)),
        day=day_offset(-1),
        minute=minute_of_day(150),
        zone=WARSAW,
    )


# --- The conversion can fail, and the caller is made to notice ----------------


def the_gap_cannot_be_ignored() -> Instant:
    """`slot_start` returns a `Result`, so a nonexistent local time is not
    something a caller can walk past — the whole point of returning it."""

    return slot_start(  # want-error: return-value
        anchor=NOON, day=day_offset(0), minute=minute_of_day(150), zone=WARSAW
    )


def both_halves_of_the_conversion_must_be_handled(anchor: Instant) -> str:
    match slot_start(
        anchor=anchor, day=day_offset(0), minute=minute_of_day(150), zone=WARSAW
    ):
        case Ok(value):
            return value.isoformat()
        case _:
            exhaustive(anchor)  # want-error: arg-type


def and_here_they_are(anchor: Instant) -> str:
    match slot_start(
        anchor=anchor, day=day_offset(0), minute=minute_of_day(150), zone=WARSAW
    ):
        case Ok(value):
            return value.isoformat()
        case Err(reason):
            return reason.kind


def a_gap_is_a_reason_and_reasons_are_frozen() -> None:
    reason = NonexistentLocalTime(
        zone="Europe/Warsaw",
        local_date=date(2026, 3, 29),
        minute_of_day=minute_of_day(150),
    )
    reason.zone = "Europe/Berlin"  # want-error: misc


def a_gap_carries_a_local_date_never_a_day_offset(
    day: DayOffset,
) -> NonexistentLocalTime:
    """A `DayOffset` is anchor-relative, so it must not leave the process — and
    a reason is the one kernel value that crosses the wire."""

    return NonexistentLocalTime(
        zone="Europe/Warsaw",
        local_date=day,  # want-error: arg-type
        minute_of_day=minute_of_day(150),
    )
