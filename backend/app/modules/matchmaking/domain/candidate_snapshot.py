"""What a search reads: one immutable container, bound once, per partition.

§13's rule is *the index cannot move underneath a running search*, and
``docs/adr/0112`` gives it its meaning in this process model: **a search takes the
container reference once, at entry, and every read goes through that binding.** A
refresh mid-search rebinds an attribute — atomic under the GIL — while the running
search keeps its container alive by reference, and the outgoing container is freed
when the last search holding it finishes. That is ``atomic.Pointer`` in Python. It
costs nothing, there is no lock, no copy and no coordination anywhere.

**Per partition, not per index.** ``(sport)`` today and ``(sport, cell)`` at
trigger 4 (``docs/adr/0101``), so the shape survives that day without a rewrite.
Generation is ``sport ∧ box ∧ gates`` and a search never spans two sports, so the
split costs nothing to make now.

**At container granularity, and never per row.** ``snapshot(partition)`` costs
54 ns; a port answering per-row questions costs **+0.58 ms** and doubles the walk
([the scale posture](../../../../docs/specs/matchmaking/scale-posture.md)). That
is why this returns the container rather than answering questions about it. It is
**not** why ``player_score`` is absent from the row: that is
``docs/adr/0111``'s rule — the index holds only what a player changes about
themselves, and a Player Score is the platform's observation of them — so the
strands are a set read over the box once per search rather than either a column
or a per-row call (``docs/adr/0140``).

**There is no derived spatial structure to rebuild.** The bounding box rejects at
18.5 ns a row against 1.00 µs per surviving candidate, which is what killed the
geo-cell bucket map — so the container is a list, and a refresh is a pointer copy
plus a few decodes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol, final, runtime_checkable

from app.modules.matchmaking.domain.candidate_index import CandidateRow, Partition
from app.modules.matchmaking.domain.index_staleness import (
    IndexFreshness,
    freshness_of,
)


@final
@dataclass(frozen=True, slots=True)
class CandidateSnapshot:
    """One partition's rows, frozen at one point in the log.

    ``snapshot_version`` **is** the tail reader's cursor and means *everything up
    to and including this is applied* — the literal sentence
    ``search-telemetry.md`` §6 demanded, true by construction rather than by
    argument, because the reader only ever advances over a contiguous prefix
    (``docs/adr/0110``). It is what makes ``docs/adr/0104``'s unexpiring search
    record reproducible, and it is the input the replay harness was missing.

    ``caught_up_at`` is when the tail reader last **knew** it was caught up, not
    when it last moved. The difference is the whole of the staleness reading: a
    healthy reader over a quiet log advances nothing and is not stale, and a dead
    one looks identical if you only watch the cursor.
    """

    partition: Partition
    rows: tuple[CandidateRow, ...]
    snapshot_version: int
    caught_up_at: datetime

    def lag_at(self, now: datetime) -> timedelta:
        """How far behind the log this container is, as a search would ask."""

        return now - self.caught_up_at

    def freshness_at(self, now: datetime) -> IndexFreshness:
        """Which rung of §18's ladder a search reading this container lands on."""

        return freshness_of(self.lag_at(now))


@runtime_checkable
class CandidateSource(Protocol):
    """Where a search gets its container. **One call, at entry, and no other.**

    Deliberately the narrowest possible surface: a source that answered questions
    *about* rows would be a source a search could call inside its walk, and the
    +0.58 ms that costs is what this shape exists to make unavailable.
    """

    def snapshot(self, partition: Partition) -> CandidateSnapshot:
        """This partition's container, as it stands right now.

        Called **once** per search and bound into the search's context. A caller
        that called it twice would be a caller the index could move underneath.

        A partition nobody has any rows for answers with an empty container
        rather than raising: *no padel players near you* is an answer, and a
        sport that has never been rated is not an error.
        """
        ...
