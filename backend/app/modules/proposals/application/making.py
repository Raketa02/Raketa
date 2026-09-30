"""Making a proposal and dealing it — **the dealer's two acts**, which no route
exposes (#538).

The engine that builds picks (#540) and posting (#546) will drive these; until
they exist, seeds and tests drive them directly, so a deck can be exercised
without waiting for an engine. Nothing here chooses *who* is dealt a game: the
caller names them, and this refuses what a game may not be dealt.

**The court hour is read, never supplied.** The share and the book-by come off
what the club sells at that hour (``SellableCourtHours``, through
``CourtHours``), so a proposal and the club cannot disagree about the price or
the deadline, and a club that is not live or is paused cannot be proposed at.

**A post is its poster's yes**, so posting asks what every yes asks of the
poster's own account — a method to charge and a live yes to spare — before the
game exists.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.proposals.application.commands import (
    DealVersionCommand,
    MakeProposalCommand,
)
from app.modules.proposals.application.guards import Guards
from app.modules.proposals.domain.errors import (
    CourtHourNotForSale,
    NotInThePool,
    PoolNotFound,
    ProposalNotFound,
)
from app.modules.proposals.domain.ports import (
    CourtHours,
    Pools,
    ProposalRepository,
)
from app.modules.proposals.domain.proposal import Proposal
from app.shared.ids import new_uuid


@final
class MakeProposal:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        pools: Pools,
        court_hours: CourtHours,
        guards: Guards,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._pools = pools
        self._court_hours = court_hours
        self._guards = guards
        self._uow = uow
        self._clock = clock

    async def execute(self, command: MakeProposalCommand) -> UUID:
        now = instant(self._clock.now())
        pool = await self._pools.find(command.pool_id)
        if pool is None:
            raise PoolNotFound()
        poster = command.poster_id
        if poster is not None and not await self._guards.in_the_pool(pool, [poster]):
            raise NotInThePool()
        offered = await self._court_hours.offered(
            command.club_id, sport=command.sport, start=command.start, now=now
        )
        if offered is None:
            raise CourtHourNotForSale()
        proposal = Proposal.make(
            proposal_id=command.proposal_id or new_uuid(),
            pool=pool,
            origin=command.origin,
            poster_id=poster,
            sport=command.sport,
            kind=command.kind,
            club_id=command.club_id,
            start=offered.start,
            share_grosze=offered.share_grosze,
            book_by=offered.book_by,
            at=now,
        )
        if poster is not None:
            await self._guards.refuse_an_unchargeable_yes(poster, proposal, now=now)
        for named in command.versions:
            await _deal(self._guards, proposal, named, at=now)
        await self._proposals.save(proposal)
        await self._uow.commit()
        return proposal.proposal_id


@final
class DealVersion:
    """Deal a game still filling to more people — once half its seats are In,
    as a new version, or after a no, into the version it left a seat on (the
    mechanics §6.2–§6.3, #540)."""

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

    async def execute(self, command: DealVersionCommand) -> int:
        """Answers the version's number."""

        now = instant(self._clock.now())
        proposal = await loaded(self._proposals, command.proposal_id)
        number = await _deal(
            self._guards,
            proposal,
            command.player_ids,
            at=now,
            into=command.into_version,
        )
        await self._proposals.save(proposal)
        await self._uow.commit()
        return number


async def _deal(
    guards: Guards,
    proposal: Proposal,
    named: Sequence[UUID],
    *,
    at: Instant,
    into: int | None = None,
) -> int:
    players = tuple(named)
    await guards.refuse_a_version_that_does_not_fit(proposal, players, at=at)
    return proposal.deal(players, at=at, into=into).number


async def loaded(proposals: ProposalRepository, proposal_id: UUID) -> Proposal:
    """The proposal, or ``proposal_not_found`` for an id with no stream."""

    proposal = await proposals.load(proposal_id)
    if proposal is None:
        raise ProposalNotFound()
    return proposal
