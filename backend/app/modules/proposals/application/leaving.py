"""A player who leaves a group leaves its pool, and **their yeses there are
withdrawn** (the mechanics §19: *You leave a group — your yeses there are
withdrawn. Your booked games stay.*).

**Told, never asked.** ``groups`` does not know a pool exists
(``.importlinter``), so the leaving reaches this context through the outbox,
as a subscriber to the group's own event, and the withdrawals commit with the
delivery that caused them. Each is the ordinary ``YesWithdrawn`` a tap on
*Withdraw* records — free and silent — dated at the leaving, and a yes on a
game that already stopped filling is left as it is.

Until the delivery lands, a yes from the leaver is refused already: a yes asks
the pool who is in it now.

**A game waiting for its club is not booked yet** (#543), so the leaver's yes on
it is withdrawn too, and the request with it — as their own *Leave* would.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.proposals.domain.ports import (
    ClubRequests,
    ProposalDirectory,
    ProposalRepository,
)
from app.modules.proposals.domain.proposal import Standing


@final
class WithdrawALeaversYeses:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        requests: ClubRequests,
    ) -> None:
        self._proposals = proposals
        self._directory = directory
        self._requests = requests

    async def execute(self, *, pool_id: UUID, player_id: UUID, at: Instant) -> int:
        """Withdraw every live yes of this player in this pool. Answers how many
        were withdrawn. **No commit**: the delivery's transaction is the
        boundary."""

        withdrawn = 0
        for yes in await self._directory.live_yeses_of(player_id, now=at):
            if yes.pool_id != pool_id:
                continue
            proposal = await self._proposals.load(yes.proposal_id)
            if proposal is None or proposal.standing_at(at) is not Standing.FILLING:
                continue
            was_waiting = proposal.waiting_for_the_club
            proposal.withdraw_yes(player_id, at=at)
            await self._proposals.save(proposal)
            if was_waiting and not proposal.waiting_for_the_club:
                await self._requests.withdraw(
                    proposal.proposal_id, player_ids=(player_id,), at=at
                )
            withdrawn += 1
        return withdrawn
