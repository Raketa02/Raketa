"""The developer's clock: what a scrub does, and who is allowed to have one.

`ScrubbableClock` exists because the seeded week is a fixed week in September
2026 and nothing in the product could stand inside it (`Raketa02/Raketa#134`,
ADR-0092). Two properties carry the whole design and each is asserted here
against a base clock this file controls, because the interesting half of *"time
still passes"* cannot be observed reliably against a real one in a few
microseconds:

**It displaces, it does not freeze.** A scrub sets an offset. The host's clock
keeps running underneath it, so every deadline the system has stays a deadline.
The alternative — a clock pinned to an instant — would show the seeded week and
animate none of it, which is the opposite of what somebody scrubbing to Tuesday
evening is trying to look at.

**Which clock a process runs on is decided once.** `build_clock` is the only
answer to *what time does this deployment think it is*, and the second half of
this file is about that: off by default, one object per process when on, and a
named way to put it back that `tests/conftest.py` calls after every test.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.bootstrap.composition import (
    build_clock,
    build_scrubbable_clock,
    forget_the_movable_clock,
)
from app.core.config import Settings
from app.infrastructure.clock import ScrubbableClock, SystemClock
from app.kernel import Clock, Instant, instant

#: An instant on the seeded week: Tuesday 8 September 2026, 21:30 UTC — half an
#: hour after the squash match ends, which is when `match-played-and-unscored`
#: is waiting for a score and `match-with-a-score-on-the-table` is waiting for an
#: answer. The one thing the wall clock cannot be on any day.
TUESDAY_EVENING: Instant = instant(datetime(2026, 9, 8, 21, 30, tzinfo=timezone.utc))

#: Somewhere plainly before the seeded week, to scrub backwards from.
LAST_YEAR: Instant = instant(datetime(2025, 3, 1, 9, 0, tzinfo=timezone.utc))


class _Base:
    """A clock this file winds by hand, standing in for the host's."""

    def __init__(self, at: Instant) -> None:
        self._at = at

    def now(self) -> Instant:
        return self._at

    def tick(self, by: timedelta) -> None:
        self._at = instant(self._at + by)


@pytest.fixture
def base() -> _Base:
    return _Base(instant(datetime(2026, 8, 24, 10, 0, tzinfo=timezone.utc)))


@pytest.fixture
def clock(base: _Base) -> ScrubbableClock:
    return ScrubbableClock(base)


# --- What a scrub does ------------------------------------------------------


def test_an_unscrubbed_clock_is_the_one_underneath_it(clock, base) -> None:
    """Zero displacement is not a special case; it is the arithmetic."""

    assert clock.now() == base.now()
    assert clock.displaced_by == 0


def test_a_scrub_stands_the_clock_where_it_was_told(clock) -> None:
    assert clock.scrub_to(TUESDAY_EVENING) != 0
    assert clock.now() == TUESDAY_EVENING


def test_time_still_passes_after_a_scrub(clock, base) -> None:
    """The property the whole choice rests on.

    A seat claim's five minutes, a commitment deadline, a result window: every
    one of them is a comparison against `now`, and a clock that stopped would
    make the week a photograph. Ninety minutes of host time is ninety minutes of
    scrubbed time, exactly — this is an offset, and offsets do not drift.
    """

    clock.scrub_to(TUESDAY_EVENING)
    base.tick(timedelta(minutes=90))

    assert clock.now() == instant(TUESDAY_EVENING + timedelta(minutes=90))


def test_a_scrub_can_run_backwards(clock) -> None:
    """Nothing about the direction is special, and the seeded week is both.

    On a laptop in March the week is ahead; on the same laptop next year it is
    behind. A signed displacement is what makes those the same operation.
    """

    displaced = clock.scrub_to(LAST_YEAR)

    assert displaced < 0
    assert clock.now() == LAST_YEAR


def test_a_second_scrub_moves_from_the_host_and_not_from_the_first(clock) -> None:
    """Absolute, never cumulative — *put the clock here*, not *move it by this*.

    The bug this refuses is the one nobody would see: two scrubs to the same
    instant landing a week apart, because the second was measured from the
    first.
    """

    clock.scrub_to(LAST_YEAR)
    clock.scrub_to(TUESDAY_EVENING)

    assert clock.now() == TUESDAY_EVENING


def test_releasing_gives_the_host_clock_back(clock, base) -> None:
    clock.scrub_to(TUESDAY_EVENING)

    given_up = clock.release()

    assert given_up != 0
    assert clock.displaced_by == 0
    assert clock.now() == base.now()


def test_the_host_clock_is_readable_through_a_scrub(clock, base) -> None:
    """So the route can answer *where you are* and *where you really are* at once."""

    clock.scrub_to(TUESDAY_EVENING)

    assert clock.base_now() == base.now()
    assert clock.now() != clock.base_now()


def test_it_satisfies_the_kernel_protocol(clock) -> None:
    """Structural, so nothing declares it — which is why it is asserted.

    Nothing above the composition root can tell this from `SystemClock`, and
    that is the property the design rests on: a use case takes a `Clock`, and a
    clock somebody moved is still a clock.
    """

    assert isinstance(clock, Clock)


def test_the_displacement_is_whole_seconds(clock) -> None:
    """`moved` is the kernel's one mover and its currency is `Seconds`.

    So a scrub keeps the host's own sub-second phase rather than landing on a
    round number — the same way the wall clock reads a second and some
    microseconds. Nothing in the system compares below the minute.
    """

    clock.scrub_to(TUESDAY_EVENING)

    assert isinstance(clock.displaced_by, int)


def test_it_reads_a_real_host_clock_when_given_one() -> None:
    """The fixtures above are a stand-in; this is the thing itself."""

    clock = ScrubbableClock(SystemClock())
    clock.scrub_to(TUESDAY_EVENING)

    assert abs((clock.now() - TUESDAY_EVENING).total_seconds()) < 1


# --- Which clock a process runs on ------------------------------------------


def wiring(**overrides) -> Settings:
    return Settings(_env_file=None, APP_ENV="local", **overrides)


def test_a_process_is_on_the_wall_clock_unless_it_was_asked_otherwise() -> None:
    """The default, and the only thing CI ever builds."""

    assert isinstance(build_clock(wiring()), SystemClock)


def test_asking_for_a_scrubbable_clock_gets_one() -> None:
    assert isinstance(build_clock(wiring(CLOCK_SCRUBBABLE=True)), ScrubbableClock)


def test_every_reader_in_the_process_gets_the_same_movable_clock() -> None:
    """The reason it is not built per call, stated as the failure it prevents.

    A clock built fresh per request would forget every scrub as the response was
    written, and the symptom would be a `POST /_clock` that answered 200 and
    changed nothing. The delivery worker is on this same object too, which is
    what keeps a scrubbed week's deadlines firing.
    """

    settings = wiring(CLOCK_SCRUBBABLE=True)

    first = build_clock(settings)
    second = build_clock(settings)

    assert first is second


def test_the_anchor_starts_the_clock_inside_the_seeded_week() -> None:
    """`make up` against a seeded database lands on the week, not beside it."""

    clock = build_scrubbable_clock(
        wiring(CLOCK_SCRUBBABLE=True, CLOCK_SCRUB_TO=TUESDAY_EVENING)
    )

    assert abs((clock.now() - TUESDAY_EVENING).total_seconds()) < 1


def test_a_scrubbable_clock_with_no_anchor_starts_on_the_wall() -> None:
    clock = build_scrubbable_clock(wiring(CLOCK_SCRUBBABLE=True))

    assert clock.displaced_by == 0


def test_two_anchors_are_two_clocks() -> None:
    """Two applications in one process — which is what a test run is.

    Keyed on the anchor rather than on nothing, so a suite that boots a second
    application configured for a different instant does not inherit the first
    one's week.
    """

    first = build_scrubbable_clock(
        wiring(CLOCK_SCRUBBABLE=True, CLOCK_SCRUB_TO=TUESDAY_EVENING)
    )
    second = build_scrubbable_clock(
        wiring(CLOCK_SCRUBBABLE=True, CLOCK_SCRUB_TO=LAST_YEAR)
    )

    assert first is not second


def test_the_process_clock_can_be_put_back() -> None:
    """The seam `tests/conftest.py` calls after every test.

    The one real cost of this design is that a clock a request can move is a
    clock a test can forget to put back. This is the answer, and it is asserted
    here rather than trusted: a scrub that survived into the next test would
    move that test's *data*, not just its clock.
    """

    settings = wiring(CLOCK_SCRUBBABLE=True)
    build_clock(settings).scrub_to(TUESDAY_EVENING)

    forget_the_movable_clock()

    assert build_clock(settings).displaced_by == 0
