"""*Confirm your payment to keep your seat* — the reader's games still filling
whose last yes could not hold their share (the mechanics §12.2; the screens
A2.4, A9).

**Wherever they were when it happened.** The yes that filled the game may have
been somebody else's, so the refused player learns of it from an email and a
notice, never from an answer; this is where the app finds the payment to
confirm. **Only while the seat is still theirs to take**: a game that filled
without them, or is no longer filling, is not here — its payment was let go.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, instant
from app.modules.proposals.domain.ports import (
    ClubNames,
    ProposalDirectory,
    ProposalRepository,
)
from app.modules.proposals.domain.proposal import Proposal, ReopenReason, Standing


@final
@dataclass(frozen=True, slots=True)
class PaymentToConfirm:
    proposal: Proposal
    seat_charge_id: UUID
    reason: ReopenReason
    club_name: str | None


@final
class ReadPaymentsToConfirm:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        clubs: ClubNames,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._directory = directory
        self._clubs = clubs
        self._clock = clock

    async def execute(self, player_id: UUID) -> tuple[PaymentToConfirm, ...]:
        owed = await owed_by(
            player_id,
            proposals=self._proposals,
            directory=self._directory,
            now=instant(self._clock.now()),
        )
        names = await self._clubs.names_of(
            {proposal.club_id for proposal, _, _ in owed}
        )
        return tuple(
            PaymentToConfirm(
                proposal=proposal,
                seat_charge_id=charge_id,
                reason=reason,
                club_name=names.get(proposal.club_id),
            )
            for proposal, charge_id, reason in owed
        )


async def owed_by(
    player_id: UUID,
    *,
    proposals: ProposalRepository,
    directory: ProposalDirectory,
    now: Instant,
) -> list[tuple[Proposal, UUID, ReopenReason]]:
    """Every game still filling on which this player has a payment to confirm,
    with the charge and why it was refused — soonest first. Home counts them
    among the games that need the player (#542)."""

    owed: list[tuple[Proposal, UUID, ReopenReason]] = []
    for proposal_id in await directory.reopened_for(player_id, now=now):
        proposal = await proposals.load(proposal_id)
        if proposal is None or proposal.standing_at(now) is not Standing.FILLING:
            continue
        reopened = proposal.reopened.get(player_id)
        if reopened is None or reopened.payment_to_confirm is None:
            continue
        owed.append((proposal, reopened.payment_to_confirm, reopened.reason))
    return owed
