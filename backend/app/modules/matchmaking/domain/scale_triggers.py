"""Trigger 4, as arithmetic. **Measured, never guessed at.**

``scale-posture.md`` §4 named two triggers and said the thing that makes them
worth having: *both ship instrumented in the first build*, because **a trigger
that requires somebody to go and measure fires late, which is the same disease
as a claim with no trigger.** Trigger 1 — scoring contending with the request —
went with the searches that scored (#579). This module is what is left: the
thresholds and the one reading taken against them, with no clock, no logger and
no event loop in it, so what fires is a property a test can state rather than a
timing a test would have to reproduce.

**4 — the index no longer fits beside the API.** Fires when ``bytes_per_row ×
rows × workers`` passes **50%** of the container's memory limit. Recomputed at
every index load.

**The reading changes nothing.** It warns and never refuses: it is the number
the escalation ladder in ``scale-posture.md`` §5 is climbed on, and the ladder
is somebody's decision.

**What is deliberately not here.** No wall-clock bound is asserted anywhere in
the suite: that is a metric, and a metric in a test suite on a shared runner is
a mute waiting to happen. What the suite asserts is this arithmetic over
injected numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

#: The measured cost of one indexed row as ``__slots__`` objects
#: (``scale-posture.md`` §1). **Not 160** — §7.2's figure is wrong three
#: different ways — and not 43, which is the ``array``-packed answer this
#: trigger *fires to authorise* rather than the state it measures.
#:
#: **And not 782, which is what this said from the day it was written** (#276).
#: That figure was measured, and it was measured against §7.2's *specified* row:
#: two ``int`` bitmasks for the tags and the grid, scalar area columns, epoch
#: ints, a shard key. ``CandidateRow`` has never had that shape — it holds two
#: tuples of strings, a tuple of ``IndexedArea``, four ``datetime`` objects and
#: no shard key at all. The number below is the first one taken against the type
#: this constant is about, by
#: ``docs/research/bench/matcher-scale/candidate_row_bench.py``, which
#: **imports** the row rather than copying it: 1 991 by ``tracemalloc`` over
#: 31 250 rows, 2 159 by the RSS cross-check.
#:
#: **Half of it is strings nobody needed a second copy of** — 996 of the 1 991,
#: which sharing the closed vocabularies would give back. That is a change
#: to the projection and not to this constant, which measures the row as it is
#: actually built; the argument is in ``candidate_snapshot_source``, beside the
#: code that would carry it, and the bench prints both figures so the saving is
#: measured before anyone decides to spend it.
#:
#: **One input to it is an assumption, and it is the one that moves the answer.**
#: ``availability`` is the most expensive field on the row — a tuple plus a
#: string per ticked cell — so how much of the grid a player fills sets the
#: total, and there are no real players to measure. The bench uses
#: ``app/seeds/cohort.py``'s density, the only one this repository states (mean
#: 6.2 of 21 cells), and **prints the elasticity rather than hiding it**: 3 cells
#: is 1 779 a row and 21 is 2 938, so trigger 4 moves between ~28 000 and
#: ~17 000 players across that range. A figure quoted without its assumption is
#: how the 782 above survived, so this one is quoted with it.
#:
#: **Re-measured at 2 016 on 2026-09-15, when the row gained the intro**
#: (``docs/adr/0170``) — one ``str`` or ``None``, so its whole cost is the share
#: of players who wrote a line times the line. That share is the second stated
#: assumption in the bench, taken from the cohort again (seven of forty-one,
#: mean 54 characters); the bench prints the elasticity beside it, and the most
#: the field can ever cost — everybody at the 100-character cap — is 2 149.
#:
#: **This is not urgent.** The correction moves trigger 4 from ~64 000 players
#: to ~25 000, against a platform whose largest environment is a laptop, and the
#: error it fixes was in the direction of firing *late* rather than of a wrong
#: refusal. What makes it worth having done is that the old figure was quoted in
#: seven files as a measurement while being a measurement of something else.
BYTES_PER_ROW = 2016

#: §4's *50% of the container memory limit*. Half, so that the index and
#: everything the API needs beside it are budgeted separately rather than the
#: index being allowed to spend the room requests are served from.
MEMORY_TRIGGER_FRACTION = 0.5

#: §1's *candidate rows ≈ 2.5 × players*, and the reason the table says **write
#: every threshold in rows, never in players**: rows are what the arithmetic
#: reads, and the player figure is the sentence a human recognises. It is used
#: to say *roughly 25 000 players* on the way out and never on the way in.
ROWS_PER_PLAYER = 2.5

#: ``docs/adr/0112`` struck the ``× 2`` that budgeted a refresh peak holding two
#: copies of every row: the refresh is a delta that copies row *references*, so
#: the steady state never holds two. **The multiplier is 1 and it is named**, so
#: that a refresh implementation which stops sharing references is a change to
#: this constant and not a rediscovery of the argument.
REFRESH_COPIES_HELD = 1


@final
@dataclass(frozen=True, slots=True)
class IndexFootprint:
    """Trigger 4's reading, recomputed at every index load.

    **It warns and never refuses.** An index that has outgrown half the container
    is a capacity decision — ``scale-posture.md`` §5's memory ladder, whose first
    rung is sharing the closed-vocabulary strings at decode (half the row) and
    whose second is ``array``-packed columns at 43 bytes a row — and a process
    that refused to load its index over it would take the platform down to avoid
    using memory it had been given.
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
        of it: **roughly 25 000 players at four workers on a 1 GB container.**
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
