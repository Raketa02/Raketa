"""*Which rooms are these?* One set read, and it is over the rows.

The rooms themselves are folded from ``event_store`` like every other aggregate
here; what this adds is the **lookup**, and the lookup is on the conversation row
because that is where ``booking_id`` and ``game_id`` are indexed.

**One question about the union, never one per booking**, which is the shape
every set read in this codebase takes. The order is not part of the answer: the
list is ordered by its last entry (``docs/adr/0148`` §11), which is a fold and
belongs to the use case.

**The whole stream of each room is folded**, and it is bounded by the room rather
than by the platform: a conversation is destroyed within days of the evening it
was arranging (``docs/adr/0153``), which is the difference ``docs/adr/0148`` §6
draws between a record and a room, applied to what a read costs.
"""

from __future__ import annotations

from typing import Collection, Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.ports import ConversationRepository
from app.modules.conversations.infrastructure.conversation_model import (
    ConversationORM,
)


class SqlAlchemyConversationDirectory:
    """``ConversationDirectory`` over the conversation rows."""

    def __init__(
        self, *, session: AsyncSession, conversations: ConversationRepository
    ) -> None:
        self._session = session
        self._conversations = conversations

    async def for_bookings(
        self, booking_ids: Collection[UUID]
    ) -> tuple[Conversation, ...]:
        if not booking_ids:
            return ()
        found = await self._session.execute(
            select(ConversationORM.conversation_id)
            .where(ConversationORM.booking_id.in_(tuple(booking_ids)))
            # Ordered so that two identical requests fold the same rooms in the
            # same order (``docs/adr/0105`` §1) — nothing downstream can observe
            # it, because the use case sorts, which is why the rule is stated on
            # the traversal rather than on what happens to be visible.
            .order_by(ConversationORM.opened_at, ConversationORM.conversation_id)
        )
        return await self._folded(found.scalars().all())

    async def every_room(self) -> tuple[Conversation, ...]:
        """Every room the store still holds, oldest first.

        **No narrowing, because there is nothing to narrow on**: a room's end is
        derived from its own stream, so the sweep folds each one and decides.
        What keeps the walk affordable is that a conversation is destroyed
        rather than kept, so this table is the size of what is live.
        """

        found = await self._session.execute(
            select(ConversationORM.conversation_id).order_by(
                ConversationORM.opened_at, ConversationORM.conversation_id
            )
        )
        return await self._folded(found.scalars().all())

    async def for_game(self, game_id: UUID) -> Conversation | None:
        """The room this game belongs to, **with its row locked**.

        Its callers are tellings that write — the *played* line, and the
        call-off that destroys the room — so this takes the lock the append
        needs, exactly as ``for_booking`` does.
        """

        found = await self._session.execute(
            select(ConversationORM.conversation_id)
            .where(ConversationORM.game_id == game_id)
            .with_for_update()
        )
        conversation_id = found.scalars().first()
        if conversation_id is None:
            return None
        return await self._conversations.load(conversation_id)

    async def _folded(self, ids: Iterable[UUID]) -> tuple[Conversation, ...]:
        rooms = []
        for conversation_id in ids:
            room = await self._conversations.load(conversation_id)
            if room is not None:
                rooms.append(room)
        return tuple(rooms)
