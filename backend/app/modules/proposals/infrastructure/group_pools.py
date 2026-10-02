"""``Pools`` over the pools projection and the groups' own directory.

**A group's pool is filed under the group's id**, so a group's id finds its pool
whether or not a proposal has been made in it — the ``pools`` row is written by
the first one (``EventSourcedProposalRepository``), and a pool with a row is
answered off it.

Who is in a group's pool is read off ``GroupDirectory`` — the groups context's
own read of its members projection — and never by joining its table: **the
members now**, so somebody who left the group has left its pool. **Every group
is a pool**, so the pools there are are the groups there are — and the group a
pool is names a booking's *where it came from* on its club's page (#547).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import exhaustive
from app.modules.groups.domain.ports import GroupDirectory
from app.modules.proposals.domain.club_bookings import BookedFrom
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

    async def every(self) -> Sequence[Pool]:
        return [
            Pool(id=group_id, kind=PoolKind.GROUP)
            for group_id in await self._groups.every()
        ]

    async def members_of(self, pool: Pool) -> tuple[UUID, ...]:
        match pool.kind:
            case PoolKind.GROUP:
                listing = (await self._groups.listings([pool.id])).get(pool.id)
                return () if listing is None else listing.members
            case _:
                exhaustive(pool.kind)

    async def of_player(self, player_id: UUID) -> Sequence[Pool]:
        return [
            Pool(id=group_id, kind=PoolKind.GROUP)
            for group_id in await self._groups.groups_of(player_id)
        ]


@final
class GroupPoolOrigins:
    """``PoolOrigins`` over the groups' own directory (#547): **a group's pool
    is filed under the group's id**, so the group a booking came from is its
    pool's listing — its name, and whether it is one of a club's official
    groups."""

    def __init__(self, groups: GroupDirectory) -> None:
        self._groups = groups

    async def of(self, pool_ids: Collection[UUID]) -> Mapping[UUID, BookedFrom]:
        listings = await self._groups.listings(sorted(set(pool_ids)))
        return {
            group_id: BookedFrom(name=listing.name.value, official=listing.is_official)
            for group_id, listing in listings.items()
        }
