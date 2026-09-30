"""``Pools`` over the pools projection and the groups' own directory.

**A group's pool is filed under the group's id**, so a group's id finds its pool
whether or not a proposal has been made in it — the ``pools`` row is written by
the first one (``EventSourcedProposalRepository``), and a pool with a row is
answered off it.

Who is in a group's pool is read off ``GroupDirectory`` — the groups context's
own read of its members projection — and never by joining its table: **the
members now**, so somebody who left the group has left its pool.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import exhaustive
from app.modules.groups.domain.ports import GroupDirectory
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.infrastructure.proposal_models import PoolORM


@final
class GroupPools:
    def __init__(self, *, session: AsyncSession, groups: GroupDirectory) -> None:
        self._session = session
        self._groups = groups

    async def find(self, pool_id: UUID) -> Pool | None:
        row = await self._session.get(PoolORM, pool_id)
        if row is not None:
            return Pool(id=row.id, kind=PoolKind(row.kind))
        if pool_id in await self._groups.listings([pool_id]):
            return Pool(id=pool_id, kind=PoolKind.GROUP)
        return None

    async def members_among(
        self, pool: Pool, player_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        match pool.kind:
            case PoolKind.GROUP:
                listing = (await self._groups.listings([pool.id])).get(pool.id)
                if listing is None:
                    return frozenset()
                return frozenset(listing.members) & frozenset(player_ids)
            case _:
                exhaustive(pool.kind)
