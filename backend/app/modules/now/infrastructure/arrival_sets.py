"""The new-arrivals cache, in the process that composed the screen.

**It expires and it does not invalidate**, which is ADR-0068's whole design: the
shelves' own clocks are 30 and 60 days, so fifteen minutes of lag is invisible
against them, and a cache with no invalidation path is the one shape that cannot
go wrong. There is no ``forget``, no ``clear`` and no hook on a write. Growing
one is not a small change — it is the second thing that has to be kept in step
with the truth, which is the reason the ADR left it out.

**In this process rather than in Redis**, and that is a deviation from ADR-0068's
*"Redis and Celery are already backend dependencies, so both caches have a
home"*. Redis is a dependency with no importer anywhere in this tree, so a Redis
adapter would arrive with a client, a connection lifetime, a failure policy and a
serialisation format — none of which any test in this suite can exercise, because
there is no Redis in a test run. What ships is the port and a store that is
*correct*: the entries are per process, so N workers pay N misses instead of one,
and every one of them answers from a real query. The seam is one line in the
composition root.

**Its lifetime is the application's.** It hangs off ``app.state`` rather than
being a module-level singleton, because the failure mode of the second shape is a
set surviving from one test's database into another's — invisible, and the kind
of green suite this tree spends itself avoiding.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.kernel import Clock, Instant, Minutes, instant, shifted

from app.modules.now.domain.arrivals import ARRIVAL_SET_TTL, ArrivalKey


@dataclass(frozen=True)
class _Entry:
    ids: tuple[UUID, ...]
    good_until: Instant


class InMemoryArrivalSets:
    """A dictionary with a clock beside it, and nothing else."""

    def __init__(self, *, clock: Clock, ttl: Minutes = ARRIVAL_SET_TTL) -> None:
        self._clock = clock
        self._ttl = ttl
        self._held: dict[str, _Entry] = {}

    async def get(self, key: ArrivalKey) -> tuple[UUID, ...] | None:
        entry = self._held.get(key.key)
        if entry is None:
            return None
        if instant(self._clock.now()) >= entry.good_until:
            # Dropped on the way past rather than swept: expiry is what this
            # store does, and a set of keys bounded by cities times sports times
            # two needs no eviction policy on top of it.
            del self._held[key.key]
            return None
        return entry.ids

    async def put(self, key: ArrivalKey, ids: tuple[UUID, ...]) -> None:
        self._held[key.key] = _Entry(
            ids=ids, good_until=shifted(instant(self._clock.now()), self._ttl)
        )
