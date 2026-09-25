"""``GroupDirectory`` over the groups and group-members projections.

**Two queries per answer and never one per group**: the groups asked about, then
every member of all of them in one read, ordered so each group's members come
out in the order they joined. A list of twenty groups costs two round trips, not
twenty-one.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.groups.domain.ports import GroupListing
from app.modules.groups.domain.value_objects import GroupCode, GroupName, JoinPolicy
from app.modules.groups.infrastructure.group_model import GroupMemberORM, GroupORM


class SqlAlchemyGroupDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listings(
        self, group_ids: Collection[UUID]
    ) -> Mapping[UUID, GroupListing]:
        wanted = set(group_ids)
        if not wanted:
            return {}
        rows = (
            await self._session.scalars(select(GroupORM).where(GroupORM.id.in_(wanted)))
        ).all()
        return await self._listed(rows)

    async def groups_of(self, player_id: UUID) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(GroupMemberORM.group_id)
                .where(GroupMemberORM.player_id == player_id)
                .order_by(GroupMemberORM.joined_at.desc(), GroupMemberORM.group_id)
            )
        ).all()

    async def listings_at(
        self, club_ids: Collection[UUID]
    ) -> Mapping[UUID, Sequence[GroupListing]]:
        wanted = set(club_ids)
        if not wanted:
            return {}
        rows = (
            await self._session.scalars(
                select(GroupORM).where(GroupORM.home_club_id.in_(wanted))
            )
        ).all()
        by_club: dict[UUID, list[GroupListing]] = {}
        for listing in (await self._listed(rows)).values():
            by_club.setdefault(listing.home_club_id, []).append(listing)
        return by_club

    async def _listed(self, rows: Sequence[GroupORM]) -> dict[UUID, GroupListing]:
        if not rows:
            return {}
        members: dict[UUID, list[UUID]] = {row.id: [] for row in rows}
        found = (
            await self._session.execute(
                select(GroupMemberORM.group_id, GroupMemberORM.player_id)
                .where(GroupMemberORM.group_id.in_(members))
                .order_by(GroupMemberORM.group_id, GroupMemberORM.joined_version)
            )
        ).all()
        for group_id, player_id in found:
            members[group_id].append(player_id)
        return {
            row.id: GroupListing(
                id=row.id,
                name=GroupName(row.name),
                home_club_id=row.home_club_id,
                join_policy=JoinPolicy(row.join_policy),
                owner_id=row.owner_id,
                code=GroupCode(row.code),
                members=tuple(members[row.id]),
            )
            for row in rows
        }
