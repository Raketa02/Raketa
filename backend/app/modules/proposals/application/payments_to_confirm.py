"""*Confirm your payment to keep your seat* — the reader's games still filling
whose last yes could not hold their share (the mechanics §12.2; the screens
A2.4, A9).

**Wherever they were when it happened.** The yes that filled the game may have
been somebody else's, so the refused player learns of it from an email and a
notice, never from an answer; this is where the app finds the payment to
confirm. **Only while the seat is still theirs to take**: a game that filled
without them, or is no longer filling, is not here — its payment was let go.

**Within their time to pay** (#625, #626; Q109) the seat is theirs alone and
the row names the time — *Confirm your payment by 14:40*; once it ran out, the
row stays without a time while the seat is still free to take back.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple, final
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
    #: The end of their time to pay, while it runs — ``None`` once it ran out
    #: and the seat is open to others too.
    confirm_by: Instant | None = None


class Owed(NamedTuple):
    """A payment a player has to confirm, on the game it is for."""

    proposal: Proposal
    seat_charge_id: UUID
    reason: ReopenReason
    confirm_by: Instant | None


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
        names = await self._clubs.names_of({one.proposal.club_id for one in owed})
        return tuple(
            PaymentToConfirm(
                proposal=one.proposal,
                seat_charge_id=one.seat_charge_id,
                reason=one.reason,
                club_name=names.get(one.proposal.club_id),
                confirm_by=one.confirm_by,
            )
            for one in owed
        )


async def owed_by(
    player_id: UUID,
    *,
    proposals: ProposalRepository,
    directory: ProposalDirectory,
    now: Instant,
) -> list[Owed]:
    """Every game still filling on which this player has a payment to confirm,
    with the charge, why it was refused and — within their time to pay — by
    when (#625) — soonest first. Home counts them among the games that need the
    player (#542)."""

    owed: list[Owed] = []
    for proposal_id in await directory.paying_for(player_id):
        proposal = await proposals.load(proposal_id)
        paying = None if proposal is None else proposal.paying.get(player_id)
        if (
            proposal is None
            or paying is None
            or paying.payment_to_confirm is None
            or proposal.standing_at(now) is not Standing.FILLING
        ):
            continue
        owed.append(
            Owed(
                proposal,
                paying.payment_to_confirm,
                paying.reason,
                # Past it, until the job runs, the seat is no longer theirs
                # alone: a confirmation runs their time out first.
                paying.until if now < paying.until else None,
            )
        )
    for proposal_id in await directory.reopened_for(player_id, now=now):
        proposal = await proposals.load(proposal_id)
        if proposal is None or proposal.standing_at(now) is not Standing.FILLING:
            continue
        reopened = proposal.reopened.get(player_id)
        if reopened is None or reopened.payment_to_confirm is None:
            continue
        owed.append(Owed(proposal, reopened.payment_to_confirm, reopened.reason, None))
    return sorted(owed, key=lambda one: (one.proposal.start, one.proposal.proposal_id))
