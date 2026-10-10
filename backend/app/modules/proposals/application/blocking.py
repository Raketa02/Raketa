"""A block takes back **the blocker's** yeses where the blocked player is In
(``docs/adr/0193`` §4).

**Told, never asked.** ``blocks`` does not know a proposal exists, so the block
reaches this context through the outbox, as a subscriber to ``PlayerBlocked``,
and the withdrawals commit with the delivery that caused them — the shape a
group leaver's take (``leaving.py``).

**The ordinary withdrawal, and nothing that tells it apart.** Each is the
``YesWithdrawn`` a tap on *Withdraw* records, dated at the block: free and
silent on a game still filling, picks and posts alike — a post the blocker made
carries on with the blocked player In, as when a poster withdraws with others
In. On a game **waiting for its club** the request goes with the yes, as the
blocker's own *Leave* would take it (ruled 2026-10-06), so the others In are
told the blocker left; nothing names a block.

**Only the blocker's yeses, and only where the blocked player is In.** The
blocked player's yes stands; a game they were merely dealt keeps the blocker's
yes, because the pair rule refuses them a seat beside it. **A booking the club
confirmed is never touched**: it is no longer filling, so it is not a live yes.

**A paused yes is taken back too.** Another booking that filled the blocker's
week paused it, and it is still theirs: left paused, it would come back the day
their week frees — after an unblock, beside the blocked player, and as a game's
last seat it would fill it and charge them. Withdrawn, it is the same
``YesWithdrawn``, and nothing reappears on the blocker's behalf.

**Owed by the block being recorded**, not by it still standing when the
delivery lands. A block lifted a second later still took the yeses back, so
what a block does never depends on how quickly the outbox ran; and unblocking
brings nothing back.

Until the delivery lands, the fill's own re-check keeps the pair off one court
(``fill.py``'s ``NO_LONGER_FITS``) — there, the seat that reopens is whoever
said yes later. This is what makes it the blocker's every other time.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.proposals.application.answers import withdraw_a_yes
from app.modules.proposals.domain.ports import (
    ClubRequests,
    ProposalDirectory,
    ProposalRepository,
    UndecidedCharges,
)
from app.modules.proposals.domain.proposal import Proposal, Standing


@final
class WithdrawABlockersYeses:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        requests: ClubRequests,
        undecided: UndecidedCharges,
    ) -> None:
        self._proposals = proposals
        self._directory = directory
        self._requests = requests
        self._undecided = undecided

    async def execute(self, *, blocker_id: UUID, blocked_id: UUID, at: Instant) -> int:
        """Withdraw every yes of the blocker — live or paused — on a game the
        blocked player is In on. Answers how many were withdrawn. **No commit**:
        the delivery's transaction is the boundary."""

        withdrawn = 0
        for yes in await self._directory.live_yeses_of(blocker_id, now=at):
            proposal = await self._with_them_in(yes.proposal_id, blocked_id, at=at)
            if proposal is None:
                continue
            await withdraw_a_yes(
                proposal,
                blocker_id,
                proposals=self._proposals,
                requests=self._requests,
                undecided=self._undecided,
                at=at,
            )
            withdrawn += 1
        for proposal_id in await self._directory.paused_for(blocker_id, now=at):
            proposal = await self._with_them_in(proposal_id, blocked_id, at=at)
            if proposal is None or not proposal.withdraw_paused_yes(blocker_id, at=at):
                continue
            await self._proposals.save(proposal)
            withdrawn += 1
        return withdrawn

    async def _with_them_in(
        self, proposal_id: UUID, blocked_id: UUID, *, at: Instant
    ) -> Proposal | None:
        """The game, while it is still filling with the blocked player In."""

        proposal = await self._proposals.load(proposal_id)
        if (
            proposal is None
            or proposal.standing_at(at) is not Standing.FILLING
            or blocked_id not in proposal.yeses
        ):
            return None
        return proposal
