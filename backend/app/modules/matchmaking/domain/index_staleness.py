"""How stale the candidate index may be — **two budgets, and only one bites.**

| | Value | What it is |
|---|---|---|
| §17 index staleness | p50 **2 s**, p99 **15 s** | A **target on the refresh
loop**. Missing it raises an alert. No behaviour changes |
| §18 lag < 15 min | serve normally | — |
| §18 lag 15 min – 24 h | serve, record ``index_stale``, alarm | **Internal.** On
the search record and in the structured logs, never on the wire envelope |
| §18 lag > 24 h | **refuse** — the honest empty state | A **quality** ladder,
not a safety stop |

The two were read as one number for as long as the map existed, and they are a
service level and a failure mode. Keeping them in one file with the difference
written down is cheaper than keeping them apart and hoping.

**The refusal stands on quality, and its stated reason is replaced**
(``docs/adr/0111``). §18 refused past 24 hours because *"a day-old index can put a
held or blocked player in front of somebody"* — and ``docs/adr/0095``,
``docs/adr/0098`` and ``docs/adr/0109`` between them took every live-truth fact
out of the index and put it in the search context with a backend re-verify. There
is nothing safety-critical left in here for a refusal to protect. What survives
is quality: a day-old index means stale μ, stale grids and stale intent, and a
shortlist built from those is a confident bad list — §18's own worst outcome.

Anyone who later moves a live-truth fact into the index for performance has to
come back and re-argue that, which is the point of writing the reason down rather
than the number.
"""

from __future__ import annotations

from datetime import timedelta
from enum import Enum
from typing import final

#: §17's service level on the refresh loop, in seconds. **A target, not a gate.**
#: The p50 is what the 2 s snapshot interval is tuned to; the p99 is what an
#: alert fires on. Neither changes what a search does, and neither is a rung of
#: the ladder below.
REFRESH_TARGET_P50 = 2.0
REFRESH_TARGET_P99 = 15.0

#: §18's first rung. Under this the index is simply served.
STALENESS_ALARM_AFTER = timedelta(minutes=15)

#: §18's second rung, and the only one that changes an answer. Past this the
#: search refuses rather than serving a confident bad list.
STALENESS_REFUSAL_AFTER = timedelta(hours=24)


@final
class IndexFreshness(Enum):
    """Which rung of §18's ladder an index lag lands on. **Three, never a scale.**

    A rung is not a number a caller may compare: *serve*, *serve and say so* and
    *refuse* are three different actions, and a float between them would be an
    invitation to invent a fourth.
    """

    FRESH = "FRESH"
    STALE = "STALE"
    REFUSED = "REFUSED"

    @property
    def serves(self) -> bool:
        """Whether a search may be answered from an index this stale at all."""

        return self is not IndexFreshness.REFUSED

    @property
    def records_staleness(self) -> bool:
        """Whether this rung sets ``index_stale`` on the search record.

        **Internal, always.** It reaches ``docs/adr/0104``'s search record and the
        structured logs and never ``docs/adr/0106``'s envelope: §18 itself says
        the player sees nothing at this rung, so a field on the contract would
        ship with no consumer — which is exactly what the play-screens map
        already refused for *Most reliable*.
        """

        return self is IndexFreshness.STALE


def freshness_of(lag: timedelta) -> IndexFreshness:
    """Which rung this lag lands on.

    A **negative** lag reads fresh rather than raising. Two clocks disagreeing by
    a second is a real and boring event, and refusing a search over it would make
    a clock skew look like an outage.
    """

    if lag >= STALENESS_REFUSAL_AFTER:
        return IndexFreshness.REFUSED
    if lag >= STALENESS_ALARM_AFTER:
        return IndexFreshness.STALE
    return IndexFreshness.FRESH


def misses_refresh_target(lag: timedelta) -> bool:
    """Whether the refresh loop has missed §17's p99. **Alert only.**

    Separate from ``freshness_of`` on purpose, and never called instead of it: a
    lag can miss this by an order of magnitude and still be nowhere near the
    ladder's first rung.
    """

    return lag > timedelta(seconds=REFRESH_TARGET_P99)
