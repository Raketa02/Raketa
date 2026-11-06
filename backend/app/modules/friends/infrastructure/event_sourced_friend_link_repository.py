"""The Friend link repository: the owner's stream, and the codes it carried.

The shape every aggregate repository here has (``docs/adr/0018``) — state
rebuilt by replay, the version remembered from the load and expected by the
append — plus ``friend_link_codes``, written **from the events appended** rather
than from the state: a replaced code is no longer in the state, and its row must
stay, marked not current, so it is never handed out again.

**Constructed per unit of work**: the versions it remembers belong to one.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.friends.domain.events import FriendLinkMade, FriendLinkReplaced
from app.modules.friends.domain.ids import friend_link_id
from app.modules.friends.domain.link import FriendLink
from app.modules.friends.infrastructure.friend_link_model import FriendLinkCodeORM

FRIEND_LINK_AGGREGATE = "friend_link"


class EventSourcedFriendLinkRepository:
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

    async def load(self, owner: UUID) -> FriendLink:
        stored = await self._event_store.load_stream(
            aggregate_type=FRIEND_LINK_AGGREGATE, aggregate_id=friend_link_id(owner)
        )
        link = FriendLink.from_history(owner, (record.event for record in stored))
        self._versions[link.id] = link.version
        return link

    async def save(self, link: FriendLink) -> None:
        pending = link.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=FRIEND_LINK_AGGREGATE,
            aggregate_id=link.id,
            expected_version=self._versions.get(link.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        for event in pending:
            if isinstance(event, FriendLinkReplaced):
                await self._session.execute(
                    update(FriendLinkCodeORM)
                    .where(FriendLinkCodeORM.code == event.replaced_code)
                    .values(current=False)
                )
            if isinstance(event, FriendLinkMade | FriendLinkReplaced):
                self._session.add(
                    FriendLinkCodeORM(
                        code=event.code,
                        owner_id=event.owner_id,
                        current=True,
                        made_at=event.occurred_at,
                    )
                )
        await self._session.flush()
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[link.id] = link.version
