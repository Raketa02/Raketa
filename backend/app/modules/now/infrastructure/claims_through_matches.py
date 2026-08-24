"""``Claims`` over the Matches aggregate, its claim table and the hold ladder.

The one file in Now that knows taking a seat is ``Match.open_claim``, that *is
she buying a seat somewhere else* is a query no aggregate can take, and that a
match whose occupancy moved has to be asked what its court is worth.

**It composes the existing write rather than reassembling it**, exactly as
``DeparturesThroughMatches`` does over the same aggregate. ``open_claim`` already
refuses everything that has to be refused — a terminal match, a started one, a
closed join cutoff, a seat she already holds, a match with nothing free, a seat
somebody else is alone with, and the thirty seconds after she let this one go —
and ``ResolveCourtHold`` is already the only thing allowed to move ``held_since``.

**It is ``matches.ClaimSeat`` minus the commit**, and the two rules are asked in
that use case's own order: the cross-match question first, because *"a player who
is mid-payment elsewhere should be told **that** rather than told this match is
full — the first refusal she gets should be the one that explains what to do."*
The commit belongs to Now's use case, on ``Departures``'s rule: the claim, the
hold ladder's answer and the outbox row close together or they do not close at
all.

**The ladder is asked although a claim moves no count it reads.** A claim holds no
seat (ADR-0081), so the answer is *stand* on every path — which is exactly what
``TakeSeat`` says about itself, and *almost always* is not a reason for a write
path to be the one that does not ask.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Instant

from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.domain.errors import MatchNotFound, PlayerAlreadyClaiming
from app.modules.matches.domain.ports import MatchRepository, SeatClaims


class ClaimsThroughMatches:
    """The five minutes in front of a free seat, opened and not committed."""

    def __init__(
        self,
        *,
        matches: MatchRepository,
        claims: SeatClaims,
        holds: ResolveCourtHold,
    ) -> None:
        self._matches = matches
        self._claims = claims
        self._holds = holds

    async def take(
        self, *, match_id: UUID, player_id: UUID, at: Instant
    ) -> Instant:
        match = await self._matches.get(match_id)
        if match is None:
            raise MatchNotFound()

        # Asked before the match is touched, and before the aggregate's own
        # refusals, so that the sentence she gets is the one that tells her what
        # to do. It is one indexed lookup and the aggregate's questions are free,
        # which is the wrong order on cost and the right one on what she reads.
        if await self._claims.live_for(player_id, at=at) is not None:
            raise PlayerAlreadyClaiming()

        claim = match.open_claim(player_id, at=at)
        await self._holds.apply(match, at=at)
        await self._matches.save(match)
        return claim.expires_at
