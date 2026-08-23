"""The match scoring context cache, in the process that composed the screen.

**Keyed ``matchId : recordVersion``, and therefore never stale.** ADR-0068 asks
for invalidation *by version*, and that is what the key is: a seat payment bumps
the match's version, so the next ask files under a key that was never written and
pays a real read. There is no TTL, no reverse index, no ``forget`` and no hook on
a write — the invalidation is already in the key, which is the shape the
new-arrivals cache buys with fifteen minutes of lag and this one gets for nothing.

**What is worth caching is what is expensive and shared.** A context holds the
club's saturation — a reservation query over its live courts in the match's
window — and every seated player's rating, which is a stream replay each. All of
it is the same for everybody looking at that match, which is the property that
makes it cacheable at all: the moment a viewer-relative field went in, the entry
would be one viewer's answer with everybody's name on it.

**In this process rather than in Redis**, exactly as ``InMemoryArrivalSets`` is
and for the same reason: ``redis`` has no importer anywhere in this tree, so a
Redis adapter would arrive with a client, a connection lifetime, a failure policy
and a serialisation format that no test run can exercise. N workers pay N misses
instead of one, and every one of them answers from a real query.

**It is bounded, and expiring by version is why it has to be.** An entry is never
invalidated, so a match played on Tuesday would otherwise sit in memory until the
process restarted. The store holds the most recently *written* entries and drops
the oldest past its cap — an insertion order rather than a use order, because a
context that has been rewritten is a match that is moving and a match that is
moving is one whose old version can never be asked for again. The cap is a
memory bound and not a hit-rate policy: it sits far above a city's live matches,
so evicting is the exception rather than how the store works.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Mapping, Sequence
from uuid import UUID

from app.modules.now.domain.funnel import MatchScoringContext

#: How many contexts one process holds. Two thousand is roughly four times the
#: 500 live city matches both Now budgets are measured against (ADR-0069,
#: ADR-0085), so a city's whole live inventory fits several versions deep.
SCORING_CONTEXT_CAP = 2000


class InMemoryScoringContexts:
    """An ordered dictionary with a size bound, and nothing else."""

    def __init__(self, *, cap: int = SCORING_CONTEXT_CAP) -> None:
        self._cap = cap
        self._held: OrderedDict[tuple[UUID, int], MatchScoringContext] = OrderedDict()

    async def known(
        self, keys: Sequence[tuple[UUID, int]]
    ) -> Mapping[tuple[UUID, int], MatchScoringContext]:
        """Whatever of these is already held, in one call for a whole screen.

        A batch rather than a lookup per card, because retrieval learns every
        candidate's version before it needs any context: the read is one
        question about a screen, and a per-card shape would invite an adapter
        that talks over a network to make one round trip per card.
        """

        return {key: self._held[key] for key in keys if key in self._held}

    async def remember(self, contexts: Sequence[MatchScoringContext]) -> None:
        for context in contexts:
            key = (context.match_id, context.version)
            # Re-inserted rather than updated in place, so a rewritten entry is
            # youngest by insertion order and the eviction below sheds the
            # matches nothing has looked at in the longest time.
            self._held.pop(key, None)
            self._held[key] = context
        while len(self._held) > self._cap:
            self._held.popitem(last=False)
