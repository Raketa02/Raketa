"""Trigger 1's two instruments, and the container limit trigger 4 is read against.

``scale-posture.md`` §4: **both triggers ship instrumented in the first build**,
as fixed-name structured log records — *a histogram around the scoring call*, *a
``PeriodicJob`` that measures its own oversleep*, and *the trigger-4 arithmetic
recomputed at every index load*. This module is the first two plus the one
reading of the machine the third needs; the arithmetic they are read against is
``domain/scale_triggers.py``, and the log records themselves are written in
``app/bootstrap/jobs.py``.

**Why the oversleep is the loop-lag monitor.** A periodic job asks the event loop
to wake it in *n* seconds and the loop wakes it in *n + ε*; ε is time the loop
spent unable to get back to it, which is the thing scoring contends for. It costs
one subtraction per tick and needs no profiler, no signal handler and no second
thread — and it is measured *by the loop it is measuring*, which is the property
that makes it honest under load.

**The window is bounded and says when it truncated.** A worker under a load
nobody has seen could otherwise accumulate an unbounded list of floats for
fifteen minutes inside the very instrument that exists to notice that load. The
duty cycle is a running sum and stays exact whatever the ceiling does; the
percentile reads what was retained and the record carries both counts, so a
truncated p99 announces itself rather than being quoted as a reading over
everything.

**Nothing here reads a clock the domain can see.** ``time.monotonic`` is a
duration source and not a wall-clock — it has no date in it, cannot be compared
to an ``Instant``, and is injected so that a test states the elapsed time rather
than sleeping through it.
"""

from __future__ import annotations

import time
from collections import deque
from pathlib import Path
from typing import Callable, final

from app.modules.matchmaking.domain.scale_triggers import (
    TRIGGER_WINDOW,
    ScoringPressure,
    pressure_of,
)

#: How many scoring samples one window keeps for the percentile. Fifteen minutes
#: of ``matchmaking-engine.md`` §17's peak — 20 searches a second — is 18 000, so
#: the ceiling is triple a peak that has never happened and the truncation path
#: is the one nobody expects to take.
SAMPLE_CEILING = 60_000

#: cgroup v2, then v1. Read in that order because a v2 host also exposes the v1
#: tree under some configurations, and the unified hierarchy is the answer there.
CGROUP_V2_MEMORY_MAX = "sys/fs/cgroup/memory.max"
CGROUP_V1_MEMORY_LIMIT = "sys/fs/cgroup/memory/memory.limit_in_bytes"

#: cgroup v1 spells *unlimited* as a number rather than as a word — a page-aligned
#: near-2⁶³ — so anything above this is read as no limit at all rather than as a
#: container with nine exabytes in it.
UNLIMITED_ABOVE = 1 << 62


@final
class ScoringMeter:
    """Every scoring call this worker made in the window that has not closed.

    One per process, held by the lifespan beside the candidate source, for the
    same reason: a per-request meter would measure one request and a per-worker
    trigger would never be readable.
    """

    def __init__(self, *, monotonic: Callable[[], float] = time.monotonic) -> None:
        self._monotonic = monotonic
        self._scoring_ms: deque[float] = deque(maxlen=SAMPLE_CEILING)
        self._loop_lag_ms: deque[float] = deque(maxlen=SAMPLE_CEILING)
        self._observed = 0
        self._total_ms = 0.0
        self._opened_at = monotonic()

    def observe_scoring(self, milliseconds: float) -> None:
        """One scoring call, from the span the search already times.

        The same span ``latency_ms_by_stage["pipeline"]`` records, deliberately:
        a second timer around a second boundary would be a second answer to
        *what did scoring cost*, and the two would disagree the day one of them
        moved.
        """

        self._scoring_ms.append(milliseconds)
        self._observed += 1
        self._total_ms += milliseconds

    def observe_loop_lag(self, milliseconds: float) -> None:
        self._loop_lag_ms.append(milliseconds)

    @property
    def window_seconds(self) -> float:
        return self._monotonic() - self._opened_at

    def close_window(self) -> ScoringPressure:
        """Read the window against §4's bounds, and open the next one."""

        reading = pressure_of(
            tuple(self._scoring_ms),
            window_seconds=self.window_seconds,
            loop_lag_ms=tuple(self._loop_lag_ms),
            total_ms=self._total_ms,
            observed=self._observed,
        )
        self._scoring_ms.clear()
        self._loop_lag_ms.clear()
        self._observed = 0
        self._total_ms = 0.0
        self._opened_at = self._monotonic()
        return reading


@final
class ScalePressureProbe:
    """The loop-lag monitor: one tick, its own oversleep, and a window that closes.

    ``tick`` answers ``None`` for every tick inside the window and the window's
    reading on the tick that closes it. That is what keeps the job in
    ``jobs.py`` to *call this and log what comes back* — a job that decided when
    a window was over would be a second copy of this rule, in the file whose
    whole discipline is that it holds no rules at all.
    """

    def __init__(
        self,
        meter: ScoringMeter,
        *,
        interval_seconds: float,
        window_seconds: float = TRIGGER_WINDOW.total_seconds(),
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._meter = meter
        self._interval_seconds = interval_seconds
        self._window_seconds = window_seconds
        self._monotonic = monotonic
        self._last_tick: float | None = None

    def tick(self) -> ScoringPressure | None:
        now = self._monotonic()
        if self._last_tick is not None:
            # **Oversleep, never undersleep.** A tick that arrives early is the
            # loop being generous with a timer and says nothing about
            # contention; recording it as negative lag would net out exactly the
            # ticks that were late.
            overslept = (now - self._last_tick) - self._interval_seconds
            self._meter.observe_loop_lag(max(overslept, 0.0) * 1000.0)
        self._last_tick = now
        if self._meter.window_seconds < self._window_seconds:
            return None
        return self._meter.close_window()


def container_memory_limit_bytes(root: Path = Path("/")) -> int | None:
    """This container's memory limit, or ``None`` where there is not one to read.

    **Unknown is not unlimited and not zero.** A laptop and a cgroup-less host
    have no limit to be half of, so trigger 4 cannot fire there and the record
    says the limit is unknown — where reporting a comfortable fraction of a
    made-up limit would be the invented measurement this map refuses everywhere
    else.

    ``root`` is a parameter so a test can drive both hierarchies and the absent
    case without a container, which is the only way this is exercised at all
    before there is a deployment.
    """

    for relative in (CGROUP_V2_MEMORY_MAX, CGROUP_V1_MEMORY_LIMIT):
        try:
            raw = (root / relative).read_text().strip()
        except OSError:
            continue
        if raw == "max":
            return None
        try:
            limit = int(raw)
        except ValueError:
            continue
        if limit <= 0 or limit > UNLIMITED_ABOVE:
            return None
        return limit
    return None
