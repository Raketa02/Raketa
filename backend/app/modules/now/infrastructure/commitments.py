"""``Commitments`` over Matches: what the viewer is already doing, as intervals.

The narrowest read in Now. ``EnrolledMatches`` answers *what a card prints* and
pays five contexts for it; this answers three columns, because that is all
eligibility needs — an id to keep a match she is already in off a shelf, and a
pair of instants to keep a different match at the same hour off it.

**The court booking's span and not the match's start**, because a clash is about
the whole evening: two matches an hour apart at ninety minutes each are one
match she cannot play. ``kernel.match_end`` is where the span comes from, so the
shelf and the card agree about when a match is over.

**Her departures count.** ``MatchRepository.for_player`` answers a seat *or* a
departure, which is ADR-0030's leaver — and both rules want her: a match she left
is still hers by identity, and its hours are still hers by the clock until
somebody else's match is put in front of her at the same time.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Instant, match_end

from app.modules.matches.domain.ports import MatchRepository


class CommitmentsFromMatches:
    """Her own matches, as ``(id, start, end)`` and nothing else."""

    def __init__(self, matches: MatchRepository) -> None:
        self._matches = matches

    async def held_by(
        self, player_id: UUID
    ) -> tuple[tuple[UUID, Instant, Instant], ...]:
        return tuple(
            (match.id, match.start, match_end(match.as_record()))
            for match in await self._matches.for_player(player_id)
        )
