"""The Origin key, proved against the record that says so. **One resolver.**

Two gestures carry an origin — *Let's play* and *not today* — and both are
required to cite the search that surfaced the person
(``search-telemetry.md`` §4, ``docs/adr/0128``). The resolution is the same three
questions in both cases, so it is written once: two implementations would be two
answers to *what counts as proof*, and the one that drifted would be the one that
linked something as null.

**Four ways this refuses, and they are one code on purpose** — the search does
not exist, it belongs to somebody else, it was run for another sport, or it never
returned this person. Telling them apart would answer *does this ``search_id``
exist* for a stranger's id, which is the question the read-back's own 404 already
declines to answer. It also swallows the degenerate case: your own search never
returns *you*, so naming yourself lands here rather than needing a refusal of its
own.

**The position is read, never sent.** A client says which search and which
person; the backend looks up where that person sat. So the origin key is true by
construction rather than by a client being honest about where it was scrolled to,
and it always resolves against ``band = RETURNED``, because no route ever returns
a near-miss row for a player to act on.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Sport
from app.modules.matchmaking.domain.errors import OriginSearchNotFound
from app.modules.matchmaking.domain.interest import OriginKey
from app.modules.matchmaking.domain.search_store import SearchStore
from app.modules.matchmaking.domain.searches import CandidateBand


async def resolve_origin(
    searches: SearchStore,
    *,
    actor_id: UUID,
    subject_id: UUID,
    sport: Sport,
    search_id: UUID,
) -> OriginKey:
    """Where this gesture came from, or a refusal.

    ``SearchStore.find`` carries the authorization rule in its own signature —
    a search that belongs to somebody else answers exactly as one that never
    existed — and it cannot load a near miss at all, so the band predicate below
    is a statement of intent rather than the thing that enforces it.
    """

    record = await searches.find(search_id=search_id, searcher_id=actor_id)
    if record is not None and record.sport is sport:
        for row in record.candidates:
            if row.band is CandidateBand.RETURNED and row.player_id == subject_id:
                return OriginKey(search_id=search_id, position=row.position)
    raise OriginSearchNotFound(
        "no search of yours showed that player for that sport"
    )
