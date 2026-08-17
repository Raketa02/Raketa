"""The kernel's time vocabulary, and the four DST behaviours it exists for.

Everything here is tested against ``Europe/Warsaw``, because that is where
Rakieta operates and because a timezone that does not observe DST tests none of
the interesting half. The two 2026 transitions:

* **2026-03-29** — 01:00 UTC, clocks go 02:00 CET → 03:00 CEST. That local day
  is twenty-three hours long and *nothing* on it is 02:30.
* **2026-10-25** — 01:00 UTC, clocks go 03:00 CEST → 02:00 CET. That local day
  is twenty-five hours long and 02:30 happens twice.

The demo week crosses neither, which is exactly why these are written now: they
are the difference between a kernel and a demo, and the failures they prevent
are silent ones — a booking grid offering an hour with no minutes in it, and a
deadline that moves by an hour twice a year.
"""

import ast
import random
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.kernel import (
    MINUTES_PER_DAY,
    Clock,
    Err,
    Instant,
    InvariantViolated,
    MinuteOfDay,
    NonexistentLocalTime,
    Ok,
    Result,
    Unavailable,
    day_offset,
    elapsed_minutes,
    hours,
    instant,
    iso_weekday,
    local_iso_weekday,
    local_minute_of_day,
    minute_of_day,
    minutes,
    shifted,
    slot_start,
)

ROOT = Path(__file__).resolve().parents[2]

WARSAW = ZoneInfo("Europe/Warsaw")
UTC = timezone.utc

#: The spring gap and the autumn overlap, as local dates.
SPRING_FORWARD = date(2026, 3, 29)
FALL_BACK = date(2026, 10, 25)

CET = timedelta(hours=1)
CEST = timedelta(hours=2)


def anchored_on(day: date) -> Instant:
    """An instant whose *Warsaw* date is `day`, safely mid-afternoon."""

    return instant(datetime(day.year, day.month, day.day, 12, 0, tzinfo=UTC))


def started(anchor: Instant, day: int, minute: int) -> Instant:
    """`slot_start` for a coordinate the caller asserts is not in a gap."""

    result = slot_start(
        anchor=anchor,
        day=day_offset(day),
        minute=minute_of_day(minute),
        zone=WARSAW,
    )
    assert isinstance(result, Ok), result
    return result.value


# --- An instant is an aware UTC datetime, and naive is refused ----------------


def test_an_aware_utc_datetime_is_an_instant_unchanged() -> None:
    value = datetime(2026, 8, 16, 9, 30, tzinfo=UTC)
    assert instant(value) == value
    assert instant(value).tzinfo is UTC


def test_a_naive_datetime_is_refused_and_the_message_names_it() -> None:
    """The classic bug this type exists to make unwritable."""

    with pytest.raises(InvariantViolated) as raised:
        instant(datetime(2026, 8, 16, 9, 30))
    assert "2026" in str(raised.value)


def test_a_tzinfo_that_offers_no_offset_is_still_naive() -> None:
    """`tzinfo is not None` is not the standard library's definition of aware.

    A `tzinfo` whose `utcoffset()` returns `None` is a naive datetime wearing a
    hat, and it is the case a one-half check waves through.
    """

    class Hat(tzinfo):
        def utcoffset(self, dt: datetime | None) -> timedelta | None:
            return None

        def dst(self, dt: datetime | None) -> timedelta | None:
            return None

        def tzname(self, dt: datetime | None) -> str | None:
            return None

    with pytest.raises(InvariantViolated):
        instant(datetime(2026, 8, 16, 9, 30, tzinfo=Hat()))


def test_an_aware_datetime_elsewhere_is_converted_not_refused() -> None:
    """Same instant, canonical spelling."""

    local = datetime(2026, 8, 16, 11, 30, tzinfo=WARSAW)
    assert instant(local) == local
    assert instant(local).tzinfo is UTC
    assert instant(local).hour == 9


# --- The integer coordinates ---------------------------------------------------


@pytest.mark.parametrize("value", [0, 1, 719, 1439])
def test_a_minute_inside_the_day_is_a_minute_of_day(value: int) -> None:
    assert minute_of_day(value) == value


@pytest.mark.parametrize("value", [-1, MINUTES_PER_DAY, MINUTES_PER_DAY + 1, 100_000])
def test_a_minute_outside_the_day_raises_and_names_the_value(value: int) -> None:
    with pytest.raises(InvariantViolated) as raised:
        minute_of_day(value)
    assert str(value) in str(raised.value)


def test_a_negative_day_offset_is_legal_because_history_is_yesterday() -> None:
    assert day_offset(-1) == -1
    assert day_offset(-365) == -365
    assert day_offset(0) == 0


@pytest.mark.parametrize("value", [1, 2, 3, 4, 5, 6, 7])
def test_a_day_of_the_week_is_iso_numbered(value: int) -> None:
    """Monday 1 through Sunday 7, the numbering `date.isoweekday` uses."""

    assert iso_weekday(value) == value
    assert date(2026, 8, 17).isoweekday() == 1


@pytest.mark.parametrize("value", [-1, 0, 8, 100])
def test_a_day_outside_the_week_raises_and_names_the_value(value: int) -> None:
    with pytest.raises(InvariantViolated) as raised:
        iso_weekday(value)
    assert str(value) in str(raised.value)


def test_a_duration_is_signed() -> None:
    assert minutes(90) == 90
    assert minutes(-90) == -90
    assert hours(12) == 720
    assert hours(-12) == -720


@pytest.mark.parametrize(
    "make", [minute_of_day, day_offset, minutes, hours, iso_weekday]
)
def test_a_bool_is_never_a_coordinate(make: object) -> None:
    """`bool` is a subclass of `int`, so `True` would silently mean one."""

    with pytest.raises(InvariantViolated):
        make(True)  # type: ignore[operator]


# --- The single conversion -----------------------------------------------------


def test_day_zero_is_the_anchors_local_date_not_its_utc_date() -> None:
    """23:00 UTC on a Saturday is already Sunday in Warsaw."""

    anchor = instant(datetime(2026, 8, 15, 23, 0, tzinfo=UTC))
    assert anchor.astimezone(WARSAW).date() == date(2026, 8, 16)
    assert started(anchor, 0, 600).astimezone(WARSAW).date() == date(2026, 8, 16)


@pytest.mark.parametrize("offset", [-400, -30, -1, 0, 1, 30, 400])
def test_a_day_offset_moves_whole_calendar_days(offset: int) -> None:
    anchor = anchored_on(date(2026, 8, 16))
    expected = date(2026, 8, 16) + timedelta(days=offset)
    assert started(anchor, offset, 600).astimezone(WARSAW).date() == expected


def test_a_minute_becomes_that_local_wall_time() -> None:
    started_at = started(anchored_on(date(2026, 8, 16)), 0, 9 * 60 + 45)
    local = started_at.astimezone(WARSAW)
    assert (local.hour, local.minute) == (9, 45)


# --- Reading an instant back on a local clock face ------------------------------


def test_both_readers_answer_for_the_local_day_and_not_the_utc_one() -> None:
    """22:30 UTC on a Sunday is already **Monday, 00:30** in Warsaw.

    The two hours a day where a weekday read off the instant's own date is wrong,
    and the reason `local_iso_weekday` exists beside `local_minute_of_day` rather
    than being left to a caller with an `astimezone` and an `isoweekday`.
    """

    late = instant(datetime(2026, 8, 23, 22, 30, tzinfo=UTC))
    assert late.isoweekday() == 7
    assert local_iso_weekday(late, WARSAW) == 1
    assert local_minute_of_day(late, WARSAW) == 30


def test_the_two_readers_are_the_inverse_of_the_conversion(
) -> None:
    """A week of coordinates out and back: the day and the minute both survive.

    `slot_start` is the one way in and these two are the way out, so this is the
    round trip stated over both halves — an off-by-one in either would show up on
    exactly one of the seven days or at exactly one minute of the day.
    """

    anchor = anchored_on(date(2026, 8, 17))  # a Monday in Warsaw
    for offset in range(7):
        for minute in (0, 1, 599, 600, 1110, 1439):
            started_at = started(anchor, offset, minute)
            assert local_minute_of_day(started_at, WARSAW) == minute
            expected = (date(2026, 8, 17) + timedelta(days=offset)).isoweekday()
            assert local_iso_weekday(started_at, WARSAW) == expected


def test_the_local_weekday_follows_the_zone_it_is_asked_in() -> None:
    """One instant, two zones, two answers — which is what a zone argument means."""

    late = instant(datetime(2026, 8, 23, 22, 30, tzinfo=UTC))
    assert local_iso_weekday(late, WARSAW) == 1
    assert local_iso_weekday(late, ZoneInfo("Europe/London")) == 7


def test_the_readers_survive_a_daylight_saving_change() -> None:
    """01:30 UTC on the spring-forward day is 03:30 in Warsaw, not 02:30.

    Read with the winter offset it would be an hour that does not exist that day,
    which is the failure `slot_start` returns an `Err` for — so the two halves of
    the round trip have to agree about the offset or the grid and the card do not.
    """

    after_the_gap = instant(datetime(2026, 3, 29, 1, 30, tzinfo=UTC))
    assert local_minute_of_day(after_the_gap, WARSAW) == 3 * 60 + 30
    assert local_iso_weekday(after_the_gap, WARSAW) == 7


# --- DST: the gap ---------------------------------------------------------------


def test_a_nonexistent_local_time_is_a_returned_unavailability() -> None:
    """02:30 does not exist on 2026-03-29 in Warsaw. Python does not say so."""

    result = slot_start(
        anchor=anchored_on(SPRING_FORWARD),
        day=day_offset(0),
        minute=minute_of_day(150),
        zone=WARSAW,
    )
    assert isinstance(result, Err)
    assert result.reason == NonexistentLocalTime(
        zone="Europe/Warsaw",
        local_date=SPRING_FORWARD,
        minute_of_day=MinuteOfDay(150),
    )
    assert result.reason.kind == "nonexistent_local_time"


def test_the_gap_is_exactly_the_hour_that_was_skipped() -> None:
    """Sixty refusals, and the sixty-first minute either side is a slot.

    An off-by-one here removes a bookable hour from the grid, or offers one that
    does not exist; both are invisible until a real booking lands on the edge.
    """

    anchor = anchored_on(SPRING_FORWARD)
    refused = [
        minute
        for minute in range(MINUTES_PER_DAY)
        if isinstance(
            slot_start(
                anchor=anchor,
                day=day_offset(0),
                minute=minute_of_day(minute),
                zone=WARSAW,
            ),
            Err,
        )
    ]
    assert refused == list(range(120, 180))


def test_the_day_before_and_after_the_gap_are_whole() -> None:
    for offset in (-1, 1):
        anchor = anchored_on(SPRING_FORWARD)
        refused = [
            minute
            for minute in range(MINUTES_PER_DAY)
            if isinstance(
                slot_start(
                    anchor=anchor,
                    day=day_offset(offset),
                    minute=minute_of_day(minute),
                    zone=WARSAW,
                ),
                Err,
            )
        ]
        assert refused == []


def test_the_gap_carries_a_local_date_and_never_the_day_offset() -> None:
    """A `DayOffset` is anchor-relative, so it must not leave the process."""

    result = slot_start(
        anchor=anchored_on(SPRING_FORWARD + timedelta(days=3)),
        day=day_offset(-3),
        minute=minute_of_day(150),
        zone=WARSAW,
    )
    assert isinstance(result, Err)
    assert result.reason.local_date == SPRING_FORWARD
    assert not hasattr(result.reason, "day")
    assert not hasattr(result.reason, "day_offset")


def test_the_reason_is_frozen() -> None:
    reason = NonexistentLocalTime(
        zone="Europe/Warsaw",
        local_date=SPRING_FORWARD,
        minute_of_day=MinuteOfDay(150),
    )
    with pytest.raises(FrozenInstanceError):
        reason.zone = "Europe/Berlin"  # type: ignore[misc]


def test_the_unavailable_union_now_has_a_member() -> None:
    """It shipped as `Never`. A `Result[T, Unavailable]` can now fail."""

    result: Result[int, Unavailable] = Err(
        NonexistentLocalTime(
            zone="Europe/Warsaw",
            local_date=SPRING_FORWARD,
            minute_of_day=MinuteOfDay(150),
        )
    )
    assert isinstance(result, Err)


# --- DST: the overlap -----------------------------------------------------------


def test_an_ambiguous_local_time_resolves_to_the_earlier_offset() -> None:
    """02:30 happens twice on 2026-10-25. Two people must get the same slot."""

    started_at = started(anchored_on(FALL_BACK), 0, 150)
    assert started_at == datetime(2026, 10, 25, 0, 30, tzinfo=UTC)
    assert started_at.astimezone(WARSAW).utcoffset() == CEST


def test_the_ambiguous_resolution_is_the_same_on_every_call() -> None:
    anchor = anchored_on(FALL_BACK)
    resolved = {started(anchor, 0, minute) for _ in range(5) for minute in (120, 150)}
    assert resolved == {
        datetime(2026, 10, 25, 0, 0, tzinfo=UTC),
        datetime(2026, 10, 25, 0, 30, tzinfo=UTC),
    }


def test_the_later_of_the_two_02_30s_is_simply_not_a_coordinate() -> None:
    """A twenty-five hour day still has 1440 coordinates, all distinct.

    The repeated hour is unreachable through `slot_start` by construction — the
    alternative, exposing it, would need a coordinate the type does not have.
    """

    anchor = anchored_on(FALL_BACK)
    reached = {started(anchor, 0, minute) for minute in range(MINUTES_PER_DAY)}
    assert len(reached) == MINUTES_PER_DAY
    assert datetime(2026, 10, 25, 1, 30, tzinfo=UTC) not in reached


# --- The round trip -------------------------------------------------------------


@pytest.mark.parametrize("day", [SPRING_FORWARD, FALL_BACK], ids=["spring", "autumn"])
def test_every_minute_of_a_boundary_day_round_trips_or_is_refused(day: date) -> None:
    """The exhaustive half: 1440 coordinates on each of the two hard days."""

    anchor = anchored_on(day)
    for minute in range(MINUTES_PER_DAY):
        result = slot_start(
            anchor=anchor,
            day=day_offset(0),
            minute=minute_of_day(minute),
            zone=WARSAW,
        )
        if isinstance(result, Err):
            assert day == SPRING_FORWARD and 120 <= minute < 180, (day, minute)
            continue
        assert local_minute_of_day(result.value, WARSAW) == minute, (day, minute)


def test_a_seeded_walk_over_a_year_of_coordinates_round_trips() -> None:
    """The broad half: a seeded pseudo-random walk, no property library.

    Reproducible from the seed printed in the assertion, which is the repo's
    existing pattern (`test_racketskill_properties.py`).
    """

    anchor = anchored_on(date(2026, 1, 1))
    refused = 0
    for seed in range(2000):
        rng = random.Random(seed)
        day = rng.randint(-400, 400)
        minute = rng.randrange(MINUTES_PER_DAY)
        result = slot_start(
            anchor=anchor,
            day=day_offset(day),
            minute=minute_of_day(minute),
            zone=WARSAW,
        )
        if isinstance(result, Err):
            # A refusal is only allowed to be the gap. Warsaw's is 02:00–02:59
            # every year, so this is structural rather than a count the walk
            # got lucky on — 800 days holds two gaps, which is 120 coordinates
            # out of 1 152 000, and a 2000-sample walk finds around none.
            refused += 1
            assert 120 <= minute < 180, f"seed {seed}: day {day}, minute {minute}"
            assert result.reason.minute_of_day == minute
            continue
        assert local_minute_of_day(result.value, WARSAW) == minute, (
            f"seed {seed}: day {day}, minute {minute}"
        )
    assert refused < 10, "the walk is landing in gaps far more often than it should"


# --- Elapsed time, never wall-clock subtraction ---------------------------------


def test_a_twelve_hour_deadline_is_twelve_elapsed_hours_across_the_gap() -> None:
    """The failure that binds people who have already paid to a match an hour
    early or late, twice a year.

    10:00 on the short day minus twelve *elapsed* hours is 21:00 the evening
    before, not 22:00 — the day lost an hour in between. Wall-clock subtraction
    gives 22:00 and is wrong by exactly that hour.
    """

    slot = started(anchored_on(SPRING_FORWARD), 0, 10 * 60)
    deadline = shifted(slot, hours(-12))
    local = deadline.astimezone(WARSAW)

    assert (local.date(), local.hour, local.minute) == (
        SPRING_FORWARD - timedelta(days=1),
        21,
        0,
    )
    assert local.hour != 22, "this is wall-clock subtraction, not elapsed time"
    assert elapsed_minutes(deadline, slot) == hours(12)


def test_elapsed_minutes_across_the_long_day_counts_the_repeated_hour() -> None:
    """Midnight to midnight over the autumn overlap is twenty-five hours."""

    anchor = anchored_on(FALL_BACK)
    assert elapsed_minutes(started(anchor, 0, 0), started(anchor, 1, 0)) == hours(25)


def test_elapsed_minutes_across_the_short_day_is_twenty_three_hours() -> None:
    anchor = anchored_on(SPRING_FORWARD)
    assert elapsed_minutes(started(anchor, 0, 0), started(anchor, 1, 0)) == hours(23)


def test_elapsed_minutes_is_signed_and_floored() -> None:
    start = instant(datetime(2026, 8, 16, 9, 0, tzinfo=UTC))
    assert elapsed_minutes(start, start) == 0
    assert elapsed_minutes(start, shifted(start, minutes(90))) == 90
    assert elapsed_minutes(shifted(start, minutes(90)), start) == -90

    # Floored, not truncated toward zero: monotonic in `end`, with no flat spot
    # straddling zero, which is what makes a "has an hour passed yet" rule
    # behave the same either side of the boundary.
    assert elapsed_minutes(start, Instant(start + timedelta(seconds=59))) == 0
    assert elapsed_minutes(start, Instant(start - timedelta(seconds=1))) == -1


def test_a_sold_duration_survives_the_gap_while_its_wall_clock_end_moves() -> None:
    """A ninety-minute slot beginning at 01:30 on the short day.

    The court is booked for an hour and a half, not until a particular clock
    face: the wall clock reads 01:30 → 04:00, two and a half hours apart, and
    ninety minutes is what elapsed and what was sold.
    """

    start = started(anchored_on(SPRING_FORWARD), 0, 90)
    end = shifted(start, minutes(90))

    assert elapsed_minutes(start, end) == 90
    assert start.astimezone(WARSAW).utcoffset() == CET
    assert end.astimezone(WARSAW).utcoffset() == CEST
    assert (end.astimezone(WARSAW).hour, end.astimezone(WARSAW).minute) == (4, 0)


def test_a_sold_duration_survives_the_overlap_too() -> None:
    """And the other direction: 02:30 → 03:00 on the clock is still ninety."""

    start = started(anchored_on(FALL_BACK), 0, 150)
    end = shifted(start, minutes(90))
    local_end = end.astimezone(WARSAW)

    assert elapsed_minutes(start, end) == 90
    assert (local_end.hour, local_end.minute) == (3, 0)
    assert local_end.utcoffset() == CET


# --- The clock is passed, and scrubbing it reproduces outputs -------------------


class ScrubbableClock:
    """A clock a test moves. The whole reason `Clock` is an interface."""

    def __init__(self, at: Instant) -> None:
        self._at = at

    def set(self, at: Instant) -> None:
        self._at = at

    def now(self) -> Instant:
        return self._at


def a_days_grid(clock: Clock) -> tuple[Instant | NonexistentLocalTime, ...]:
    """Something that reads the clock exactly once and then computes."""

    now = clock.now()
    grid = []
    for minute in range(0, MINUTES_PER_DAY, 30):
        result = slot_start(
            anchor=now, day=day_offset(0), minute=minute_of_day(minute), zone=WARSAW
        )
        grid.append(result.value if isinstance(result, Ok) else result.reason)
    return tuple(grid)


def test_a_clock_satisfies_the_kernel_protocol() -> None:
    assert isinstance(ScrubbableClock(anchored_on(SPRING_FORWARD)), Clock)


def test_a_clock_moved_forwards_and_back_reproduces_identical_output() -> None:
    """Determinism, which every falsification claim in the system rests on."""

    spring = anchored_on(SPRING_FORWARD)
    clock = ScrubbableClock(spring)

    first = a_days_grid(clock)
    clock.set(anchored_on(FALL_BACK))
    elsewhere = a_days_grid(clock)
    clock.set(spring)

    assert a_days_grid(clock) == first
    assert elsewhere != first, "the scrub moved nothing — this proves nothing"


# --- Every timezone question has one place to be asked --------------------------


def _modules_of(tree: Path) -> list[Path]:
    return sorted(tree.rglob("*.py"))


def _imports_zoneinfo(path: Path) -> bool:
    parsed = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [] if node.level else [node.module or ""]
        else:
            continue
        if any(name.split(".")[0] == "zoneinfo" for name in names):
            return True
    return False


def test_no_engine_builds_a_zone_and_every_engine_may_hold_one() -> None:
    """An engine is *given* its zone, exactly as it is given `now`.

    `Zone` is exported so that a club snapshot can name the type without importing
    `zoneinfo`, and the export is what makes this walk necessary: constructing one
    resolves an IANA name against the tz database, which is a read of configuration
    and of the filesystem, and ADR-0015's purity rules forbid an engine both. The
    contracts cannot see this — the name comes from `app.kernel`, which engines may
    import — so it is a walk.
    """

    engines = _modules_of(ROOT / "app" / "engines")
    builders = [
        f"{path.relative_to(ROOT)}:{node.lineno}"
        for path in engines
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in ("Zone", "ZoneInfo")
    ]
    assert builders == [], builders
    assert len(engines) >= 10, "the walk has lost the tree it is claiming about"
    assert any(
        "Zone" in path.read_text(encoding="utf-8") for path in engines
    ), "no engine names a zone at all — this walk is asserting nothing"


def test_zoneinfo_is_imported_in_exactly_one_module() -> None:
    """*"Nothing else constructs an instant from coordinates"*, checked.

    A second `zoneinfo` import in `app/` is a second answer to a timezone
    question, and the two will disagree about a DST boundary long before anyone
    compares them.
    """

    walked = _modules_of(ROOT / "app")
    importers = sorted(
        str(path.relative_to(ROOT)) for path in walked if _imports_zoneinfo(path)
    )
    assert importers == ["app/kernel/time.py"]
    assert len(walked) >= 100, "the walk has lost the tree it is claiming about"


def test_a_day_offset_never_reaches_a_persistence_or_wire_module() -> None:
    """It is anchor-relative, so a stored one is a number whose meaning moves.

    Vacuous today — nothing consumes the kernel's time module yet — so the walk
    counts what it read, and this becomes a real gate the first time an ORM
    model or a response schema reaches for a coordinate.
    """

    boundaries = [
        path
        for path in _modules_of(ROOT / "app")
        if any(part in ("infrastructure", "presentation") for part in path.parts)
    ]
    offenders = [
        str(path.relative_to(ROOT))
        for path in boundaries
        if "DayOffset" in path.read_text(encoding="utf-8")
        or "day_offset" in path.read_text(encoding="utf-8")
    ]
    assert not offenders, (
        "a day offset is in-memory only — it leaves the process as an Instant "
        "or a local date, never as a number:\n" + "\n".join(offenders)
    )
    assert len(boundaries) >= 20, "the walk has lost the tree it is claiming about"
    assert any("orm" in path.name or "models" in path.name for path in boundaries)


# --- What is deliberately not here ----------------------------------------------


def test_no_peak_part_of_day_or_week_start_function_exists() -> None:
    """Each needs a constant with no owner yet, and none has a consumer.

    ADR-0022 may place the peak boundary in club configuration; inventing one
    here would answer a domain question this repo has left open, in the layer
    that is hardest to change later.
    """

    import app.kernel as kernel

    absent = ("peak", "part_of_day", "week_start", "start_of_week", "off_peak")
    named = [
        name for name in kernel.__all__ if any(word in name.lower() for word in absent)
    ]
    assert named == []
