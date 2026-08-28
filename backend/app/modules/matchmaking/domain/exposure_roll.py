"""What *shown more often than most* means, this week, in this sport.

The exposure floor has three rungs (``matchmaking-engine.md`` §14.2): shown zero
times lifts, shown once to three times lifts a little, and **shown more than the
week's ninetieth percentile docks**. The first two read a count; the third reads
a *distribution*, and a distribution is not something a search can afford to
compute — so the roll computes one scalar an hour and the search reads it.

This module is that scalar's arithmetic and nothing else. It is named
``busy_threshold_of`` rather than ``busy_threshold`` because the ledger beside it
has a method of that name: one **computes** the threshold from a distribution and
one **reads back** the one a roll published, and a single spelling for both would
make the roll's own body ambiguous about which it meant. It is pure and takes
no store, because the percentile is the only part of the roll that can be wrong
in a way the job's own logs would not show: a loop that read the wrong key logs
an empty bucket, and a loop that computed the wrong quantile logs a number that
looks exactly like the right one.
"""

from __future__ import annotations

from math import ceil
from typing import Collection

from app.kernel import invariant

#: The quantile the dock rung reads. **Ninetieth**, from §14.2 — the rung is
#: *relieve the concentrated tenth*, and it is a ruleset row's worth of judgement
#: living here rather than in the ruleset because it is not a weight: moving it
#: changes which players count as busy, not what being busy is worth.
EXPOSURE_BUSY_PERCENTILE = 90


def busy_threshold_of(counts: Collection[int]) -> int | None:
    """The appearance count a player has to **exceed** to read as busy.

    **Nearest-rank, never interpolated.** An interpolated quantile over integer
    appearance counts lands between two of them, and a threshold of 4.6
    appearances is a number nobody in the bucket can have and no log line can be
    read against. The rung is *shown more times than this*, so the bound has to
    be a count somebody actually has.

    ``None`` for an empty bucket, which is the honest answer rather than zero:
    a zero would put every player in the pool above the threshold in the exact
    state — nobody shown to anybody yet — that the floor's other two rungs exist
    to lift them out of.

    Deterministic in its input and independent of iteration order, which is what
    makes the roll idempotent and safe beside itself: two processes reading the
    same bucket a moment apart publish the same scalar, and one reading a bucket
    that grew by an appearance publishes a scalar the next tick converges on
    anyway.
    """

    for count in counts:
        invariant(count >= 0, f"a negative exposure count in the bucket: {count}")

    if not counts:
        return None

    ordered = sorted(counts)
    # Ceil-of-the-rank, so the smallest bucket that can have a tail — one player
    # — reads that player's own count rather than an index below the list.
    rank = ceil(EXPOSURE_BUSY_PERCENTILE / 100 * len(ordered))
    return ordered[rank - 1]
