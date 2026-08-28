"""The two scale triggers, as arithmetic. **Measured, never guessed at.**

``scale-posture.md`` §4 names two triggers and says the thing that makes them
worth having: *both ship instrumented in the first build*, because **a trigger
that requires somebody to go and measure fires late, which is the same disease
as a claim with no trigger.** This module is the arithmetic half of that — the
thresholds, and the two readings taken against them — with no clock, no logger
and no event loop in it, so what fires is a property a test can state rather
than a timing a test would have to reproduce.

**1 — request latency contends with scoring.** Fires when the p99 of one
scoring call passes **20 ms**, or the duty cycle passes **0.25**, on one worker
over fifteen minutes. Read by the scoring meter, on a periodic job.

**4 — the index no longer fits beside the API.** Fires when ``bytes_per_row ×
rows × workers`` passes **50%** of the container's memory limit. Recomputed at
every index load.

**Neither reading changes what a search does.** Trigger 1 is a log record; trigger
4 warns and never refuses. They are the two numbers the escalation ladder in
``scale-posture.md`` §5 is climbed on, and the ladder is somebody's decision — a
process that started truncating candidate blocks by itself the first time a
runner was busy would be taking that decision without the argument.

**What is deliberately not here.** No wall-clock bound, no p99 and no
empty-result rate is asserted anywhere in the suite: those are metrics, and a
metric in a test suite on a shared runner is a mute waiting to happen. What the
suite asserts is this arithmetic over injected samples — which is not a
measurement of this machine and does not become one when the runner is loaded.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol, Sequence, final

#: §4's first half: the p99 of **one scoring call**, in milliseconds. A search
#: is ~2.8 ms and a doubles line-up ~11.4 ms on the machine the posture was
#: measured on, derated to 5.6–8.4 and 23–34 on a small cloud vCPU — so this
#: bound is crossed by the line-up first, and crossing it is what says the
#: scoring cost has started to contend with the request rather than ride in it.
SCORING_P99_TRIGGER_MS = 20.0

#: §4's second half: the fraction of wall-clock one worker spends inside the
#: scorer. **0.07 at §17's peak**, so the trigger has a factor of three and a
#: half of headroom in it and is a statement about a load nobody has seen.
DUTY_CYCLE_TRIGGER = 0.25

#: *on one worker over 15 min* — the window both halves are read over. Long
#: enough that one slow line-up cannot fire it and short enough that a Thursday
#: evening is several windows rather than a corner of one.
TRIGGER_WINDOW = timedelta(minutes=15)

#: The measured cost of one indexed row as ``__slots__`` objects
#: (``scale-posture.md`` §1). **Not 160** — §7.2's figure is wrong three
#: different ways — and not 43, which is the ``array``-packed answer this
#: trigger *fires to authorise* rather than the state it measures.
BYTES_PER_ROW = 782

#: §4's *50% of the container memory limit*. Half, so that the index and
#: everything the API needs beside it are budgeted separately rather than the
#: index being allowed to spend the room requests are served from.
MEMORY_TRIGGER_FRACTION = 0.5

#: §1's *candidate rows ≈ 2.5 × players*, and the reason the table says **write
#: every threshold in rows, never in players**: rows are what the arithmetic
#: reads, and the player figure is the sentence a human recognises. It is used
#: to say *roughly 64 000 players* on the way out and never on the way in.
ROWS_PER_PLAYER = 2.5

#: ``docs/adr/0112`` struck the ``× 2`` that budgeted a refresh peak holding two
#: copies of every row: the refresh is a delta that copies row *references*, so
#: the steady state never holds two. **The multiplier is 1 and it is named**, so
#: that a refresh implementation which stops sharing references is a change to
#: this constant and not a rediscovery of the argument.
REFRESH_COPIES_HELD = 1


def p99_ms(samples: Sequence[float]) -> float:
    """The 99th percentile of a sample, by **nearest rank**.

    Nearest rank rather than an interpolation, because the reading is compared
    against a bound and interpolating invents a value between two measurements
    that were both taken. An empty sample reads ``0.0`` — *nothing was scored*
    is not a pressure reading, and the caller has ``samples`` to tell the two
    apart with.
    """

    if not samples:
        return 0.0
    ordered = sorted(samples)
    rank = math.ceil(0.99 * len(ordered))
    return ordered[max(rank, 1) - 1]


@final
@dataclass(frozen=True, slots=True)
class ScoringPressure:
    """Trigger 1's reading over one window on one worker.

    Both halves are carried whichever fired, because *the p99 crossed* and *the
    duty cycle crossed* are two different escalations — the first is answered by
    ``scale-posture.md`` §5's rungs 1 and 2, the second by rung 4 — and a record
    that only said *trigger 1 fired* would send the reader to re-measure what the
    instrument already knew.
    """

    #: How many scoring calls the window saw. Carried so that a p99 over four
    #: searches is not read as the same claim as a p99 over four thousand.
    samples: int
    #: How many of them the percentile actually read. **Equal to ``samples``
    #: unless the meter's own ceiling truncated the window**, and separate from
    #: it so that a truncated p99 announces itself instead of being quoted as a
    #: reading over everything. The duty cycle below is exact either way — it is
    #: a running sum and not a sample.
    retained: int
    window_seconds: float
    scoring_p99_ms: float
    duty_cycle: float
    #: The event-loop lag monitor's own oversleep, p99. **Not part of the
    #: trigger** — it is the corroborating instrument, and the reason it is on
    #: this record is that a duty cycle rising without the loop lagging is a
    #: different story from the two moving together.
    loop_lag_p99_ms: float

    @property
    def p99_crossed(self) -> bool:
        return self.scoring_p99_ms > SCORING_P99_TRIGGER_MS

    @property
    def duty_cycle_crossed(self) -> bool:
        return self.duty_cycle > DUTY_CYCLE_TRIGGER

    @property
    def fires(self) -> bool:
        """Whether trigger 1 has fired. **Or, never and** (§4's own wording)."""

        return self.p99_crossed or self.duty_cycle_crossed


def pressure_of(
    scoring_ms: Sequence[float],
    *,
    window_seconds: float,
    loop_lag_ms: Sequence[float] = (),
    total_ms: float | None = None,
    observed: int | None = None,
) -> ScoringPressure:
    """One window's samples, read against §4's two bounds.

    The duty cycle is *time spent scoring ÷ wall-clock elapsed*, which is what
    makes it a statement about **one worker's event loop** rather than about the
    fleet: two workers each at 0.2 are not one worker at 0.4, and the trigger is
    written per worker precisely because the answer to it — rung 4's resident
    index in a process pool — is a per-worker change.

    ``total_ms`` and ``observed`` are what a meter that keeps a bounded sample
    passes in: the percentile reads what was retained, and the duty cycle reads
    every call there was. Omitted, both are read off the sample, which is the
    same answer whenever nothing was dropped.
    """

    spent = math.fsum(scoring_ms) if total_ms is None else total_ms
    elapsed_ms = window_seconds * 1000.0
    return ScoringPressure(
        samples=len(scoring_ms) if observed is None else observed,
        retained=len(scoring_ms),
        window_seconds=window_seconds,
        scoring_p99_ms=p99_ms(scoring_ms),
        duty_cycle=(spent / elapsed_ms) if elapsed_ms > 0 else 0.0,
        loop_lag_p99_ms=p99_ms(loop_lag_ms),
    )


@final
@dataclass(frozen=True, slots=True)
class IndexFootprint:
    """Trigger 4's reading, recomputed at every index load.

    **It warns and never refuses.** An index that has outgrown half the container
    is a capacity decision — ``array``-packed columns at 43 bytes a row, which
    cost 23% on the scan (``scale-posture.md`` §5) — and a process that refused
    to load its index over it would take the platform down to avoid using memory
    it had been given.
    """

    rows: int
    workers: int
    bytes_per_row: int
    #: The container's memory limit, or ``None`` where the process cannot read
    #: one. **Unknown is not unlimited**: with no limit there is no fraction to
    #: compare and the trigger cannot fire, which the record says out loud
    #: rather than reporting a comfortable zero.
    limit_bytes: int | None

    @property
    def bytes_held(self) -> int:
        return self.bytes_per_row * self.rows * self.workers * REFRESH_COPIES_HELD

    @property
    def budget_bytes(self) -> float | None:
        if self.limit_bytes is None:
            return None
        return self.limit_bytes * MEMORY_TRIGGER_FRACTION

    @property
    def fraction_of_budget(self) -> float | None:
        budget = self.budget_bytes
        if budget is None or budget <= 0:
            return None
        return self.bytes_held / budget

    @property
    def fires(self) -> bool:
        fraction = self.fraction_of_budget
        return fraction is not None and fraction > 1.0

    @property
    def rows_at_trigger(self) -> int | None:
        """How many rows this container and this worker count fire at."""

        budget = self.budget_bytes
        if budget is None or self.workers <= 0:
            return None
        return int(budget // (self.bytes_per_row * REFRESH_COPIES_HELD * self.workers))

    @property
    def players_at_trigger(self) -> int | None:
        """The same bound, in the units a human recognises it in.

        §1's *write every threshold in rows, never in players* is about the
        arithmetic, which reads rows throughout. This is the sentence at the end
        of it: **roughly 64 000 players at four workers on a 1 GB container.**
        """

        rows = self.rows_at_trigger
        if rows is None:
            return None
        return int(rows / ROWS_PER_PLAYER)


def footprint_of(*, rows: int, workers: int, limit_bytes: int | None) -> IndexFootprint:
    """Trigger 4, from the rows this worker holds and the container it is in."""

    return IndexFootprint(
        rows=rows,
        workers=workers,
        bytes_per_row=BYTES_PER_ROW,
        limit_bytes=limit_bytes,
    )


class ScoringInstrument(Protocol):
    """What a surface needs of the meter: somewhere to report one scoring call.

    A port rather than the meter itself, so the application layer depends on
    *being able to report a duration* and not on the process-wide object that
    keeps a window of them. The null case is ``None`` at the call site rather
    than a null object here — a surface with no meter is the ordinary state of
    every test in the suite, and a no-op class would be a second thing to keep
    in step with the real one.
    """

    def observe_scoring(self, milliseconds: float) -> None:
        """Record one scoring call. **Never raises, never blocks.**"""
