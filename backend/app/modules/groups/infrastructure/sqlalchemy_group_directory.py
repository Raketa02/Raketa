"""``GroupDirectory`` over the groups, group-members and join-requests
projections.

**Three queries per answer and never one per group**: the groups asked about,
then every member of all of them in one read, ordered so each group's members
come out in the order they joined, then everybody waiting on any of them, in the
order they asked. A list of twenty groups costs three round trips, not sixty-one.

**Matching a name is a scan**, as matching a club's is (``docs/adr/0182`` accepted
that by name for the clubs' copy, and the groups' copy is the same shape): the
query is folded here by the function the stored copy was folded by, and matched
with ``LIKE`` escaped so that a ``%`` a player typed is a percent sign.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.stored_time import (
    stored_instant,
    stored_instant_or_none,
)
from app.kernel import Instant
from app.modules.clubs.domain.folding import fold
from app.modules.groups.domain.ports import GroupListing
from app.modules.groups.domain.value_objects import (
    DeclaredSports,
    GroupCode,
    GroupKind,
    GroupName,
    JoinPolicy,
    WhatsAppSize,
)
from app.modules.groups.infrastructure.group_model import (
    GroupJoinRequestORM,
    GroupMemberORM,
    GroupORM,
)


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

    async def first_joined(
        self, *, after: Instant, by: Instant
    ) -> Mapping[UUID, Instant]:
        first = func.min(GroupMemberORM.joined_at)
        rows = await self._session.execute(
            select(GroupMemberORM.player_id, first)
            .group_by(GroupMemberORM.player_id)
            .having(first > after, first <= by)
        )
        return {player_id: stored_instant(joined) for player_id, joined in rows}

    async def every(self) -> Sequence[UUID]:
        return (
            await self._session.scalars(
                select(GroupORM.id).order_by(GroupORM.created_at, GroupORM.id)
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

    async def with_code(self, code: GroupCode) -> GroupListing | None:
        row = await self._session.scalar(
            select(GroupORM).where(GroupORM.code == code.value)
        )
        if row is None:
            return None
        return (await self._listed([row]))[row.id]

    async def official_at(self, club_id: UUID) -> Sequence[GroupListing]:
        rows = (
            await self._session.scalars(
                select(GroupORM).where(
                    GroupORM.home_club_id == club_id,
                    GroupORM.kind == GroupKind.OFFICIAL.value,
                )
            )
        ).all()
        return list((await self._listed(rows)).values())

    async def run_by(self, administrator_id: UUID) -> Sequence[GroupListing]:
        rows = (
            await self._session.scalars(
                select(GroupORM)
                .where(GroupORM.administrator_id == administrator_id)
                .order_by(GroupORM.created_at.desc(), GroupORM.id)
            )
        ).all()
        listed = await self._listed(rows)
        return [listed[row.id] for row in rows]

    async def named(self, text: str) -> Mapping[UUID, frozenset[UUID]]:
        found = (
            await self._session.execute(
                select(GroupORM.home_club_id, GroupORM.id).where(
                    GroupORM.name_folded.contains(fold(text), autoescape=True)
                )
            )
        ).all()
        by_club: dict[UUID, set[UUID]] = {}
        for club_id, group_id in found:
            by_club.setdefault(club_id, set()).add(group_id)
        return {club_id: frozenset(ids) for club_id, ids in by_club.items()}

    async def _listed(self, rows: Sequence[GroupORM]) -> dict[UUID, GroupListing]:
        if not rows:
            return {}
        members: dict[UUID, list[UUID]] = {row.id: [] for row in rows}
        joined_at: dict[UUID, dict[UUID, datetime]] = {row.id: {} for row in rows}
        found = (
            await self._session.execute(
                select(
                    GroupMemberORM.group_id,
                    GroupMemberORM.player_id,
                    GroupMemberORM.joined_at,
                )
                .where(GroupMemberORM.group_id.in_(members))
                .order_by(GroupMemberORM.group_id, GroupMemberORM.joined_version)
            )
        ).all()
        for group_id, player_id, at in found:
            members[group_id].append(player_id)
            joined_at[group_id][player_id] = at
        waiting: dict[UUID, list[UUID]] = {row.id: [] for row in rows}
        asked = (
            await self._session.execute(
                select(GroupJoinRequestORM.group_id, GroupJoinRequestORM.player_id)
                .where(GroupJoinRequestORM.group_id.in_(waiting))
                .order_by(
                    GroupJoinRequestORM.group_id,
                    GroupJoinRequestORM.requested_version,
                )
            )
        ).all()
        for group_id, player_id in asked:
            waiting[group_id].append(player_id)
        return {
            row.id: GroupListing(
                id=row.id,
                name=GroupName(row.name),
                home_club_id=row.home_club_id,
                join_policy=JoinPolicy(row.join_policy),
                owner_id=row.owner_id,
                code=GroupCode(row.code),
                members=tuple(members[row.id]),
                waiting=tuple(waiting[row.id]),
                joined_at=joined_at[row.id],
                kind=GroupKind(row.kind),
                administrator_id=row.administrator_id,
                whatsapp_size=(
                    None
                    if row.whatsapp_size is None
                    else WhatsAppSize(row.whatsapp_size)
                ),
                declared_sports=(
                    None
                    if row.declared_sports is None
                    else DeclaredSports.from_codes(row.declared_sports)
                ),
                handed_over_at=stored_instant_or_none(row.handed_over_at),
            )
            for row in rows
        }
