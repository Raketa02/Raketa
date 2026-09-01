"""The two triggers' arithmetic, over injected samples.

**Nothing here measures this machine.** Every sample below is a number written
in the test, so what is asserted is the arithmetic and the two bounds — never a
wall-clock, never a p99 of anything that actually ran, never an empty-result
rate. Those are metrics, and a metric asserted in a suite on a shared runner is
a mute waiting to happen: it goes red for the runner's reasons, somebody widens
it, and the assertion that survives says nothing. ``scale-posture.md`` §4 wants
the triggers *instrumented*, which is a different thing from asserted.
"""

from __future__ import annotations

import pytest

from app.modules.matchmaking.domain.scale_triggers import (
    BYTES_PER_ROW,
    DUTY_CYCLE_TRIGGER,
    REFRESH_COPIES_HELD,
    ROWS_PER_PLAYER,
    SCORING_P99_TRIGGER_MS,
    TRIGGER_WINDOW,
    footprint_of,
    p99_ms,
    pressure_of,
)

#: The window both halves of trigger 1 are read over, in seconds.
WINDOW = TRIGGER_WINDOW.total_seconds()

#: A gigabyte, as the posture's own arithmetic spells it — ``0.5 × 10⁹`` over
#: ``1 991 × 4`` is what produces §4's *~63 000 rows*, and reading it as a
#: gibibyte would move that figure by 7% and stop the number in the document
#: reproducing.
ONE_GB = 1_000_000_000


# ---------------------------------------------------------------------------
# Trigger 1 — the scoring call contends with the request
# ---------------------------------------------------------------------------


def test_the_percentile_is_nearest_rank_and_never_interpolates() -> None:
    """A value between two measurements is a value nobody took."""

    assert p99_ms([1.0, 2.0, 3.0, 4.0]) == 4.0
    assert p99_ms([5.0]) == 5.0


def test_an_empty_window_is_not_a_pressure_reading() -> None:
    """*Nothing was scored* reads zero, and ``samples`` is what says which."""

    quiet = pressure_of([], window_seconds=WINDOW)
    assert quiet.samples == 0
    assert quiet.scoring_p99_ms == 0.0
    assert quiet.duty_cycle == 0.0
    assert not quiet.fires


def test_a_p99_over_the_bound_fires_and_says_which_half() -> None:
    # Nearest rank over a hundred samples reads the 99th, so one slow call in
    # a hundred is inside the p99 by construction and two are not — which is
    # the percentile doing its job rather than a threshold being generous.
    hundred = [1.0] * 98 + [SCORING_P99_TRIGGER_MS + 0.1] * 2
    reading = pressure_of(hundred, window_seconds=WINDOW)
    assert reading.p99_crossed
    assert not reading.duty_cycle_crossed
    assert reading.fires


def test_the_bound_is_strict_so_the_stated_number_is_still_inside_it() -> None:
    """*p99 > 20 ms*, and 20 ms is not more than 20 ms.

    Asserted because the trigger is a sentence in a spec before it is a
    comparison in code, and ``>=`` would move the threshold by one measurement
    without anybody editing the number.
    """

    at_the_bound = pressure_of(
        [SCORING_P99_TRIGGER_MS] * 100, window_seconds=WINDOW
    )
    assert not at_the_bound.p99_crossed


def test_the_duty_cycle_is_time_scoring_over_wall_clock_on_one_worker() -> None:
    """Half a second of scoring in a ten-second window is 0.05, whatever the
    shape of the calls that produced it."""

    reading = pressure_of([10.0] * 50, window_seconds=10.0)
    assert reading.duty_cycle == pytest.approx(0.05)
    assert not reading.fires


def test_a_duty_cycle_over_the_bound_fires_on_its_own() -> None:
    """The p99 stays well inside its bound: a fleet of quick searches arriving
    fast is the shape rung 4 answers, and the p99 alone would never see it."""

    busy = pressure_of([2.0] * 1_400, window_seconds=10.0)
    assert busy.duty_cycle > DUTY_CYCLE_TRIGGER
    assert not busy.p99_crossed
    assert busy.fires


def test_the_loop_lag_rides_along_and_is_not_part_of_the_trigger() -> None:
    """A duty cycle rising without the loop lagging is a different story from
    the two moving together, so the corroborating instrument is recorded and
    never summed into the verdict."""

    reading = pressure_of(
        [1.0] * 10, window_seconds=WINDOW, loop_lag_ms=[400.0] * 10
    )
    assert reading.loop_lag_p99_ms == 400.0
    assert not reading.fires


# ---------------------------------------------------------------------------
# Trigger 4 — the index no longer fits beside the API
# ---------------------------------------------------------------------------


def test_the_trigger_reproduces_the_postures_own_stated_bound() -> None:
    """*Roughly 25 000 players at four workers on a 1 GB container.*

    The one number in ``scale-posture.md`` §4 that a reader is most likely to
    quote, re-derived here from the constants rather than restated — so a change
    to ``BYTES_PER_ROW`` or to the half-the-container budget moves this
    assertion instead of leaving the document quietly wrong. It moved once, and
    that is the whole of #276: the figure said ~64 000 while ``BYTES_PER_ROW``
    was 782, which was measured against the row ``matchmaking-engine.md`` §7.2
    *specified* and never against the row this codebase holds.
    """

    footprint = footprint_of(rows=0, workers=4, limit_bytes=ONE_GB)
    assert footprint.rows_at_trigger == 62_782
    assert footprint.players_at_trigger == 25_112


def test_the_refresh_holds_one_copy_of_a_row_and_the_multiplier_is_named() -> None:
    """``docs/adr/0112`` struck the ``× 2``: the delta copies row *references*,
    so the steady state never holds two copies. The day a refresh stops sharing
    them, this constant is what moves."""

    assert REFRESH_COPIES_HELD == 1
    footprint = footprint_of(rows=1_000, workers=2, limit_bytes=ONE_GB)
    assert footprint.bytes_held == BYTES_PER_ROW * 1_000 * 2


def test_an_index_over_half_the_container_fires() -> None:
    over = footprint_of(rows=63_000, workers=4, limit_bytes=ONE_GB)
    assert over.fires
    assert (over.fraction_of_budget or 0) > 1.0


def test_an_index_at_the_launch_citys_size_does_not_fire_but_is_no_longer_far() -> None:
    """§1's launch city — 10³–10⁴ players at ~2.5 rows each — against the same
    container the trigger is written for.

    **The headroom is the thing #276 moved.** At 782 bytes a row the top of the
    launch range sat at a sixth of the budget; at the measured 1 991 it sits at
    **two fifths** of it. It still does not fire, and the fraction is asserted
    rather than the verdict alone, because *does not fire* is the same sentence
    at 16% and at 40% and only one of them is comfortable.
    """

    launch = footprint_of(
        rows=int(10_000 * ROWS_PER_PLAYER), workers=4, limit_bytes=ONE_GB
    )
    assert not launch.fires
    assert 0.38 < (launch.fraction_of_budget or 0) < 0.42


def test_an_unreadable_limit_is_unknown_and_never_unlimited() -> None:
    """A process that cannot read a cgroup limit has no fraction to compare, and
    the record says so rather than reporting a comfortable zero."""

    unknown = footprint_of(rows=10_000_000, workers=4, limit_bytes=None)
    assert unknown.fraction_of_budget is None
    assert unknown.rows_at_trigger is None
    assert unknown.players_at_trigger is None
    assert not unknown.fires
