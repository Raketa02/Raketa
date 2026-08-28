"""The two instruments, driven by a clock a test states rather than sleeps through.

Nothing here sleeps and nothing here asserts a duration this machine produced:
the monotonic source is a list of numbers, so *fifteen minutes elapsed* is a
statement and not a wait. ``scale-posture.md`` §4 wants the triggers
**instrumented**; asserting a real p99 on a shared runner would be asserting a
metric, which is the one thing the ticket that built this deliberately does not
do.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.modules.matchmaking.domain.scale_triggers import TRIGGER_WINDOW
from app.modules.matchmaking.infrastructure.scale_instruments import (
    SAMPLE_CEILING,
    ScalePressureProbe,
    ScoringMeter,
    container_memory_limit_bytes,
)

WINDOW = TRIGGER_WINDOW.total_seconds()


class FakeMonotonic:
    """A duration source the test advances. Not a clock — it has no date in it."""

    def __init__(self) -> None:
        self.seconds = 0.0

    def __call__(self) -> float:
        return self.seconds

    def advance(self, seconds: float) -> None:
        self.seconds += seconds


# ---------------------------------------------------------------------------
# The meter


def test_a_window_reads_the_calls_it_saw_and_then_opens_a_new_one() -> None:
    time = FakeMonotonic()
    meter = ScoringMeter(monotonic=time)
    for _ in range(100):
        meter.observe_scoring(4.0)
    time.advance(WINDOW)

    closed = meter.close_window()
    assert closed.samples == 100
    assert closed.scoring_p99_ms == 4.0
    assert closed.window_seconds == WINDOW
    assert not closed.fires

    time.advance(WINDOW)
    assert meter.close_window().samples == 0


def test_the_duty_cycle_survives_the_sample_ceiling_and_the_p99_says_so() -> None:
    """A window that truncated announces it rather than being quoted as a
    reading over everything.

    The duty cycle is a running sum, so it stays exact past the ceiling — which
    matters, because the load that overflows the sample is precisely the load
    the trigger exists to notice.
    """

    time = FakeMonotonic()
    meter = ScoringMeter(monotonic=time)
    for _ in range(SAMPLE_CEILING + 10):
        meter.observe_scoring(1.0)
    time.advance(10.0)

    closed = meter.close_window()
    assert closed.samples == SAMPLE_CEILING + 10
    assert closed.retained == SAMPLE_CEILING
    assert closed.duty_cycle == (SAMPLE_CEILING + 10) / 10_000.0


# ---------------------------------------------------------------------------
# The probe — the loop lag monitor


def test_a_tick_inside_the_window_reports_nothing() -> None:
    time = FakeMonotonic()
    probe = ScalePressureProbe(
        ScoringMeter(monotonic=time), interval_seconds=1.0, monotonic=time
    )
    assert probe.tick() is None
    time.advance(1.0)
    assert probe.tick() is None


def test_the_probe_measures_its_own_oversleep() -> None:
    """A tick asked for in a second and delivered in 1.4 is 400 ms the loop
    could not get back to it, which is the contention trigger 1 is about."""

    time = FakeMonotonic()
    meter = ScoringMeter(monotonic=time)
    probe = ScalePressureProbe(meter, interval_seconds=1.0, monotonic=time)

    probe.tick()
    time.advance(1.4)
    probe.tick()

    assert meter.close_window().loop_lag_p99_ms == pytest.approx(400.0)


def test_a_tick_that_arrives_early_is_not_negative_lag() -> None:
    """Undersleep is the loop being generous with a timer and says nothing about
    contention. Recorded as a negative it would net out exactly the ticks that
    were late, so a busy worker could report a comfortable zero."""

    time = FakeMonotonic()
    meter = ScoringMeter(monotonic=time)
    probe = ScalePressureProbe(meter, interval_seconds=1.0, monotonic=time)

    probe.tick()
    time.advance(0.5)
    probe.tick()

    assert meter.close_window().loop_lag_p99_ms == 0.0


def test_the_tick_that_closes_the_window_is_the_one_that_reports() -> None:
    time = FakeMonotonic()
    meter = ScoringMeter(monotonic=time)
    probe = ScalePressureProbe(meter, interval_seconds=1.0, monotonic=time)
    meter.observe_scoring(2.0)

    assert probe.tick() is None
    time.advance(WINDOW)
    reading = probe.tick()
    assert reading is not None
    assert reading.samples == 1
    # And the next window starts empty, so a busy quarter of an hour cannot be
    # reported twice.
    time.advance(WINDOW)
    following = probe.tick()
    assert following is not None
    assert following.samples == 0


# ---------------------------------------------------------------------------
# The container limit trigger 4 is read against


def test_the_v2_limit_is_read(tmp_path: Path) -> None:
    (tmp_path / "sys/fs/cgroup").mkdir(parents=True)
    (tmp_path / "sys/fs/cgroup/memory.max").write_text("1073741824\n")
    assert container_memory_limit_bytes(tmp_path) == 1_073_741_824


def test_a_v2_container_with_no_limit_reads_unknown(tmp_path: Path) -> None:
    (tmp_path / "sys/fs/cgroup").mkdir(parents=True)
    (tmp_path / "sys/fs/cgroup/memory.max").write_text("max\n")
    assert container_memory_limit_bytes(tmp_path) is None


def test_the_v1_limit_is_read_when_there_is_no_v2_tree(tmp_path: Path) -> None:
    (tmp_path / "sys/fs/cgroup/memory").mkdir(parents=True)
    (tmp_path / "sys/fs/cgroup/memory/memory.limit_in_bytes").write_text(
        "536870912\n"
    )
    assert container_memory_limit_bytes(tmp_path) == 536_870_912


def test_v1s_numeric_spelling_of_unlimited_is_not_a_nine_exabyte_container(
    tmp_path: Path,
) -> None:
    """cgroup v1 spells *no limit* as a page-aligned near-2⁶³ rather than as a
    word, and a container with nine exabytes in it is not a thing."""

    (tmp_path / "sys/fs/cgroup/memory").mkdir(parents=True)
    (tmp_path / "sys/fs/cgroup/memory/memory.limit_in_bytes").write_text(
        "9223372036854771712"
    )
    assert container_memory_limit_bytes(tmp_path) is None


def test_a_host_with_no_cgroup_at_all_reads_unknown(tmp_path: Path) -> None:
    """A laptop. **Unknown is not unlimited** — trigger 4 simply cannot fire."""

    assert container_memory_limit_bytes(tmp_path) is None
