"""``OriginSearchQuery``'s adapter — what a search says about the court built on it.

``challenges`` may not import the matcher, and a send needs three facts that are
the search record's and nobody else's: the sport it ran for, the kind of evening
it was scored against, and the **window** derived from the grid it actually ran
on. It also needs where each invitee sat, which is the other half of every seat's
origin key.

**It reads the record and never recomputes it.** ``docs/adr/0104`` makes the
record the answer's identity, and the read-back reads it back rather than
re-running anything; a send is the same posture one screen later.

**One refusal, four causes.** ``None`` covers a search that does not exist, one
that is somebody else's, one run for another sport and one that never returned a
person named — which is exactly ``resolve_origin``'s posture and for exactly its
reason: telling them apart would answer *does this search_id exist* about a
stranger's id, one probe at a time. The sport case folds in for free, because the
sport is read *off* the record rather than compared against a client's claim.

**It resolves against ``RETURNED`` rows only.** No route ever hands a player a
near-miss row to act on, so a court containing one was never built from anything
this search showed.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID

from app.modules.challenges.domain.ports import CourtOrigin
from app.modules.matchmaking.domain.search_store import SearchStore
from app.modules.matchmaking.domain.searches import CandidateBand


@final
class SearchCourtOrigin:
    """Answers ``challenges`` about one search of the organiser's own."""

    def __init__(self, searches: SearchStore) -> None:
        self._searches = searches

    async def court_origin(
        self,
        *,
        search_id: UUID,
        organiser_id: UUID,
        invitee_ids: Collection[UUID],
    ) -> CourtOrigin | None:
        record = await self._searches.find(
            search_id=search_id, searcher_id=organiser_id
        )
        if record is None:
            return None
        positions = {
            row.player_id: row.position
            for row in record.candidates
            if row.band is CandidateBand.RETURNED
        }
        wanted = set(invitee_ids)
        if not wanted <= set(positions):
            return None
        return CourtOrigin(
            sport=record.sport,
            mode=record.mode,
            window=record.pool_description.window,
            positions={player_id: positions[player_id] for player_id in wanted},
        )
