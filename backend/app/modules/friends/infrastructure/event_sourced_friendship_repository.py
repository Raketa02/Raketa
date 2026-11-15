"""The Friendship repository: the pair's stream, its two projection rows, and
its asks for a level.

The shape every aggregate repository here has — the aggregate type spelled once,
state rebuilt by replay, the version remembered from the load and expected by
the append (``docs/adr/0018``) — plus the projection, rewritten by ``save`` from
the aggregate **as it stands** after the append, in the caller's transaction. A
pair's rows are few and wholly determined by its state, so they are replaced,
not patched event by event — and so are its ``friend_level_asks`` rows, when
an ask, its answer or its setting aside is among the events appended (#749,
#764): nothing else moves them.

**Constructed per unit of work**: the versions it remembers belong to one.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import ColumnElement, and_, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.kernel import invariant
from app.modules.friends.domain.events import (
    LevelAsked,
    LevelAskSetAside,
    LevelGot,
)
from app.modules.friends.domain.friendship import Friendship
from app.modules.friends.domain.ids import friendship_id
from app.modules.friends.domain.relation import FriendRelation
from app.modules.friends.infrastructure.friendship_model import (
    FriendLevelAskORM,
    FriendRelationORM,
)

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
        if any(
            isinstance(event, LevelAsked | LevelGot | LevelAskSetAside)
            for event in pending
        ):
            await self._project_the_asks(friendship)
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[friendship.id] = friendship.version

    async def _project(self, friendship: Friendship) -> None:
        first, second = friendship.first_id, friendship.second_id
        await self._session.execute(
            delete(FriendRelationORM).where(
                _either_way(
                    FriendRelationORM.player_id,
                    FriendRelationORM.other_id,
                    first,
                    second,
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

    async def _project_the_asks(self, friendship: Friendship) -> None:
        first, second = friendship.first_id, friendship.second_id
        await self._session.execute(
            delete(FriendLevelAskORM).where(
                _either_way(
                    FriendLevelAskORM.asker_id,
                    FriendLevelAskORM.friend_id,
                    first,
                    second,
                )
            )
        )
        for ask in friendship.level_asks:
            self._session.add(
                FriendLevelAskORM(
                    asker_id=ask.asker_id,
                    friend_id=second if ask.asker_id == first else first,
                    sport=ask.sport.value,
                    group_id=ask.group_id,
                    asked_at=ask.asked_at,
                    got_at=ask.got_at,
                    set_aside_at=ask.set_aside_at,
                )
            )
        await self._session.flush()


def _either_way(
    one: InstrumentedAttribute[UUID],
    other: InstrumentedAttribute[UUID],
    first: UUID,
    second: UUID,
) -> ColumnElement[bool]:
    """The pair's rows, whichever of the two each row is keyed from."""

    return or_(and_(one == first, other == second), and_(one == second, other == first))
