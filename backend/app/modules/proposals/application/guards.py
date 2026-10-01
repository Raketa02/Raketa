"""The checks that live outside the aggregate, shared by every act that asks
them: whether somebody may be dealt a version, and whether a yes may land.

**The In set is always pairwise fit, and these two checks are why.** A version
must fit everybody already In — every pair — and so must a yes, because the
people In can change after a card was dealt: B and E are dealt two versions of
Marek's post while only Marek is In, B says yes, and E no longer meets a game
of Marek alone (the mechanics §6.1, §7). Checking only the pairs the newcomer is
in is deliberate: a pair already In that stopped fitting — two players who
blocked each other after saying yes — is not the newcomer's refusal to carry,
and it is the fill's to read: the later of the two yeses stops counting
(``fill.py``).

**A yes needs three facts about the player's own account first**, in the order
the phone meets them: a method to charge (the setup opens), a live yes to spare
(the card springs back), and then the fit (the card has gone).
"""

from __future__ import annotations

from collections.abc import Collection
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.proposals.domain.errors import (
    LiveYesesExhausted,
    NotInThePool,
    NoLongerFits,
    PaymentMethodRequired,
    VersionDoesNotFit,
)
from app.modules.proposals.domain.limits import LIVE_YESES_PER_SPORT
from app.modules.proposals.domain.pool import Pool
from app.modules.proposals.domain.ports import (
    PlayerFit,
    Pools,
    ProposalDirectory,
    SavedMethods,
)
from app.modules.proposals.domain.proposal import Proposal


@final
class Guards:
    def __init__(
        self,
        *,
        pools: Pools,
        fit: PlayerFit,
        methods: SavedMethods,
        directory: ProposalDirectory,
    ) -> None:
        self._pools = pools
        self._fit = fit
        self._methods = methods
        self._directory = directory

    async def in_the_pool(self, pool: Pool, player_ids: Collection[UUID]) -> bool:
        wanted = frozenset(player_ids)
        return await self._pools.members_among(pool, wanted) == wanted

    async def refuse_a_version_that_does_not_fit(
        self, proposal: Proposal, named: Collection[UUID], *, at: Instant
    ) -> None:
        """Everybody named is a player of the pool, and fits everybody else on
        the version: the people In and each other."""

        if not await self.in_the_pool(proposal.pool, named):
            raise NotInThePool()
        if await self._misfits(proposal, named, at=at):
            raise VersionDoesNotFit()

    async def refuse_an_unchargeable_yes(
        self, player_id: UUID, proposal: Proposal, *, now: Instant
    ) -> None:
        """A method to charge, then a live yes to spare in the sport."""

        if not await self._methods.saved_for(player_id):
            raise PaymentMethodRequired()
        live = await self._directory.live_yes_count(
            player_id, sport=proposal.sport, now=now
        )
        if live >= LIVE_YESES_PER_SPORT:
            raise LiveYesesExhausted(
                cap=LIVE_YESES_PER_SPORT, sport=proposal.sport.value
            )

    async def refuse_a_yes_that_does_not_fit(
        self, player_id: UUID, proposal: Proposal, *, at: Instant
    ) -> None:
        if await self._misfits(proposal, [player_id], at=at):
            raise NoLongerFits()

    async def _misfits(
        self, proposal: Proposal, newcomers: Collection[UUID], *, at: Instant
    ) -> bool:
        """Whether any pair among the people In and ``newcomers`` that holds a
        newcomer does not fit — a yes being a version of one."""

        arriving = frozenset(newcomers)
        unfit = await self._fit.unfit_pairs(
            {*proposal.yeses, *arriving},
            sport=proposal.sport,
            kind=proposal.kind,
            at=at,
        )
        return any(pair & arriving for pair in unfit)
