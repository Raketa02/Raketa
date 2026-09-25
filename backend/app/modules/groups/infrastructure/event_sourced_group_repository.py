"""The Group repository: the stream, and the projections written beside it.

The same shape as the other aggregate repositories — the aggregate type spelled
once, state rebuilt by replay, the version remembered from the load and expected
by the append (``docs/adr/0018``) — plus the one thing a group needs that they do
not: **its projections are written by ``save``, in the caller's transaction**
(``docs/adr/0183`` §1), so a group is in the next list and the next search and
there is no second call to forget.

**Constructed per request**, for the reason every aggregate repository here is:
the versions it remembers belong to one unit of work.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Executable

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.clubs.domain.folding import fold
from app.modules.groups.domain.events import (
    GroupDeleted,
    GroupJoined,
    GroupLeft,
    GroupRenamed,
    JoinPolicyChanged,
    JoinRequestApproved,
    JoinRequestDeclined,
    JoinRequested,
    OwnershipPassed,
    PlayerGroupCreated,
)
from app.modules.groups.domain.group import Group
from app.modules.groups.infrastructure.group_model import (
    GroupJoinRequestORM,
    GroupMemberORM,
    GroupORM,
)
from app.shared.domain import DomainEvent

GROUP_AGGREGATE = "group"


class EventSourcedGroupRepository:
    """``GroupRepository`` over ``DomainEventStore`` and the two projections."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._session = session
        self._event_store = event_store
        self._events = events
        self._versions: dict[UUID, int] = {}

    async def load(self, group_id: UUID) -> Optional[Group]:
        stored = await self._event_store.load_stream(
            aggregate_type=GROUP_AGGREGATE, aggregate_id=group_id
        )
        if not stored:
            return None
        group = Group.from_history(record.event for record in stored)
        if group.is_deleted:
            return None
        self._versions[group.id] = group.version
        return group

    async def save(self, group: Group) -> None:
        pending = group.pull_events()
        if not pending:
            return
        expected = self._versions.get(group.id, 0)
        await self._event_store.append(
            aggregate_type=GROUP_AGGREGATE,
            aggregate_id=group.id,
            expected_version=expected,
            events=pending,
        )
        await self._events.publish_many(pending)
        for offset, event in enumerate(pending, start=1):
            await self._project(event, version=expected + offset)
        await self._session.flush()
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[group.id] = group.version

    async def _project(self, event: DomainEvent, *, version: int) -> None:
        if isinstance(event, PlayerGroupCreated):
            self._session.add(
                GroupORM(
                    id=event.group_id,
                    name=event.name,
                    name_folded=fold(event.name),
                    home_club_id=event.home_club_id,
                    join_policy=event.join_policy,
                    owner_id=event.owner_id,
                    code=event.code,
                )
            )
            # The group's row before its first member's, which references it.
            await self._session.flush()
            self._admit(event.group_id, event.owner_id, event, version)
        elif isinstance(event, GroupJoined):
            self._admit(event.group_id, event.player_id, event, version)
        elif isinstance(event, JoinRequested):
            self._session.add(
                GroupJoinRequestORM(
                    group_id=event.group_id,
                    player_id=event.player_id,
                    requested_at=event.occurred_at,
                    requested_version=version,
                )
            )
        elif isinstance(event, JoinRequestApproved):
            await self._stop_waiting(event.group_id, event.player_id)
            self._admit(event.group_id, event.player_id, event, version)
        elif isinstance(event, JoinRequestDeclined):
            await self._stop_waiting(event.group_id, event.player_id)
        elif isinstance(event, GroupLeft):
            await self._statement(
                delete(GroupMemberORM).where(
                    GroupMemberORM.group_id == event.group_id,
                    GroupMemberORM.player_id == event.player_id,
                )
            )
        elif isinstance(event, OwnershipPassed):
            await self._change(event.group_id, owner_id=event.to_id)
        elif isinstance(event, GroupRenamed):
            await self._change(
                event.group_id, name=event.name, name_folded=fold(event.name)
            )
        elif isinstance(event, JoinPolicyChanged):
            await self._change(event.group_id, join_policy=event.join_policy)
        elif isinstance(event, GroupDeleted):
            await self._forget(event.group_id)
        else:
            raise TypeError(f"Unsupported group event {event!r}")

    async def _stop_waiting(self, group_id: UUID, player_id: UUID) -> None:
        await self._statement(
            delete(GroupJoinRequestORM).where(
                GroupJoinRequestORM.group_id == group_id,
                GroupJoinRequestORM.player_id == player_id,
            )
        )

    async def _change(self, group_id: UUID, **values: object) -> None:
        await self._statement(
            update(GroupORM).where(GroupORM.id == group_id).values(**values)
        )

    async def _forget(self, group_id: UUID) -> None:
        """A deleted group leaves **no row in any of the three**: it is in no
        list and no search, and its link finds nothing (``docs/adr/0183`` §7).
        The requests and the members are deleted by name rather than left to
        the foreign keys' cascade, which SQLite does not enforce by default.

        The stream keeps the history, and nothing reads a deleted group's code
        back out of it: a new group could in principle be minted the same eight
        characters, one draw in 31⁸, and that is a chance the minter's own
        table check already takes about every live group."""

        await self._statement(
            delete(GroupJoinRequestORM).where(GroupJoinRequestORM.group_id == group_id)
        )
        await self._statement(
            delete(GroupMemberORM).where(GroupMemberORM.group_id == group_id)
        )
        await self._statement(delete(GroupORM).where(GroupORM.id == group_id))

    async def _statement(self, statement: Executable) -> None:
        # A statement, not a unit-of-work change, so whatever this save added
        # before it is flushed first — the row it touches may be one.
        await self._session.flush()
        await self._session.execute(statement)

    def _admit(
        self,
        group_id: UUID,
        player_id: UUID,
        event: PlayerGroupCreated | GroupJoined | JoinRequestApproved,
        version: int,
    ) -> None:
        self._session.add(
            GroupMemberORM(
                group_id=group_id,
                player_id=player_id,
                joined_at=event.occurred_at,
                joined_version=version,
            )
        )
