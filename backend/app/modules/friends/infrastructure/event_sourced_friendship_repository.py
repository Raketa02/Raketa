"""The Friendship repository: the pair's stream, and its two projection rows.

The shape every aggregate repository here has — the aggregate type spelled once,
state rebuilt by replay, the version remembered from the load and expected by
the append (``docs/adr/0018``) — plus the projection, rewritten by ``save`` from
the aggregate **as it stands** after the append, in the caller's transaction. A
pair's rows are few and wholly determined by its state, so they are replaced,
not patched event by event.

**Constructed per unit of work**: the versions it remembers belong to one.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.kernel import invariant
from app.modules.friends.domain.friendship import Friendship
from app.modules.friends.domain.ids import friendship_id
from app.modules.friends.domain.relation import FriendRelation
from app.modules.friends.infrastructure.friendship_model import FriendRelationORM

FRIENDSHIP_AGGREGATE = "friendship"


class EventSourcedFriendshipRepository:
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

    async def load(self, one: UUID, other: UUID) -> Friendship:
        stored = await self._event_store.load_stream(
            aggregate_type=FRIENDSHIP_AGGREGATE,
            aggregate_id=friendship_id(one, other),
        )
        friendship = Friendship.from_history(
            one, other, (record.event for record in stored)
        )
        self._versions[friendship.id] = friendship.version
        return friendship

    async def save(self, friendship: Friendship) -> None:
        pending = friendship.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=FRIENDSHIP_AGGREGATE,
            aggregate_id=friendship.id,
            expected_version=self._versions.get(friendship.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        await self._project(friendship)
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[friendship.id] = friendship.version

    async def _project(self, friendship: Friendship) -> None:
        first, second = friendship.first_id, friendship.second_id
        await self._session.execute(
            delete(FriendRelationORM).where(
                or_(
                    and_(
                        FriendRelationORM.player_id == first,
                        FriendRelationORM.other_id == second,
                    ),
                    and_(
                        FriendRelationORM.player_id == second,
                        FriendRelationORM.other_id == first,
                    ),
                )
            )
        )
        for side in (first, second):
            relation = friendship.relation_of(side)
            if relation is FriendRelation.NONE:
                continue
            other = second if side == first else first
            if relation is FriendRelation.FRIEND:
                self._session.add(
                    FriendRelationORM(
                        player_id=side,
                        other_id=other,
                        relation=relation.value,
                        since=friendship.friends_since,
                        set_aside=False,
                    )
                )
                continue
            request = invariant(friendship.request, "a request row, nothing asked")
            self._session.add(
                FriendRelationORM(
                    player_id=side,
                    other_id=other,
                    relation=relation.value,
                    since=request.asked_at,
                    set_aside=relation is FriendRelation.ASKED_YOU
                    and request.set_aside,
                    made_from=request.where.made_from.value,
                    group_id=request.where.group_id,
                    sport=None
                    if request.where.sport is None
                    else request.where.sport.value,
                )
            )
        await self._session.flush()
