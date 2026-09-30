"""A player's three answers to a card: **yes**, **no**, and a yes taken back
(the mechanics §6, §10.2; the screens A2.4, A3.2).

**All three are silent.** Nothing here is told to anybody: the others learn of a
yes from the card, and a no leaves no trace but the card's absence (§6.4). Each
is one transaction on one stream, and a repeated tap records nothing.

**A yes asks the game first, then the player's account, then the people In** —
a stranger learns nothing about anybody's card, a player with no method is sent
to save one before a live yes is counted, and whether they still fit the people
In is the last thing asked because it is the only question that costs reads of
other people.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.proposals.application.commands import AnswerProposalCommand
from app.modules.proposals.application.guards import Guards
from app.modules.proposals.application.making import loaded
from app.modules.proposals.domain.errors import ProposalNotFound
from app.modules.proposals.domain.ports import ProposalRepository


@final
@dataclass(frozen=True, slots=True)
class YesAnswer:
    """What a yes left: the seats still open on the game. Nought is a game
    every seat said yes to — the one the fill books (#541)."""

    proposal_id: UUID
    open_seats: int


@final
class SayYes:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        guards: Guards,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._guards = guards
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AnswerProposalCommand) -> YesAnswer:
        now = instant(self._clock.now())
        player_id = command.player_id
        proposal = await loaded(self._proposals, command.proposal_id)
        if proposal.may_say_yes(player_id, at=now):
            # Somebody who has left the group has left its pool: the card is
            # nothing to them any more, which is the stranger's answer.
            if not await self._guards.in_the_pool(proposal.pool, [player_id]):
                raise ProposalNotFound()
            await self._guards.refuse_an_unchargeable_yes(player_id, proposal, now=now)
            await self._guards.refuse_a_yes_that_does_not_fit(
                player_id, proposal, at=now
            )
            proposal.say_yes(player_id, at=now)
            await self._proposals.save(proposal)
            await self._uow.commit()
        return YesAnswer(
            proposal_id=proposal.proposal_id, open_seats=proposal.open_seats
        )


@final
class SayNo:
    def __init__(
        self, *, proposals: ProposalRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._proposals = proposals
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AnswerProposalCommand) -> None:
        proposal = await loaded(self._proposals, command.proposal_id)
        proposal.say_no(command.player_id, at=instant(self._clock.now()))
        await self._proposals.save(proposal)
        await self._uow.commit()


@final
class WithdrawYes:
    """*Withdraw* on a You're In row: free and silent until the game fills.
    **Not asked of the pool** — somebody who left the group can still take a
    yes back that is theirs."""

    def __init__(
        self, *, proposals: ProposalRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._proposals = proposals
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AnswerProposalCommand) -> None:
        proposal = await loaded(self._proposals, command.proposal_id)
        proposal.withdraw_yes(command.player_id, at=instant(self._clock.now()))
        await self._proposals.save(proposal)
        await self._uow.commit()
