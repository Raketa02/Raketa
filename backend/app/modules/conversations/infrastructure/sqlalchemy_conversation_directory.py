"""*Which rooms are these?* One set read, and it is over the rows.

The rooms themselves are folded from ``event_store`` like every other aggregate
here; what this adds is the **lookup**, and the lookup is on the conversation row
because that is where ``challenge_id`` and ``game_id`` are indexed.

**One question about the union, never one per challenge**, which is the shape
every set read in this codebase takes. The order is not part of the answer: the
list is ordered by its last entry (``docs/adr/0148`` §11), which is a fold and
belongs to the use case.

**The whole stream of each room is folded**, and it is bounded by the room rather
than by the platform: a conversation is destroyed within days of the evening it
was arranging (``docs/adr/0153``), which is the difference ``docs/adr/0148`` §6
draws between a record and a room, applied to what a read costs. The challenges
list already folds an aggregate per row for the same reason.
"""

from __future__ import annotations

from typing import Collection
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

    async def for_challenges(
        self, challenge_ids: Collection[UUID]
    ) -> tuple[Conversation, ...]:
        if not challenge_ids:
            return ()
        found = await self._session.execute(
            select(ConversationORM.conversation_id)
            .where(ConversationORM.challenge_id.in_(tuple(challenge_ids)))
            # Ordered so that two identical requests fold the same rooms in the
            # same order (``docs/adr/0105`` §1) — nothing downstream can observe
            # it, because the use case sorts, which is why the rule is stated on
            # the traversal rather than on what happens to be visible.
            .order_by(ConversationORM.opened_at, ConversationORM.conversation_id)
        )
        rooms = []
        for conversation_id in found.scalars().all():
            room = await self._conversations.load(conversation_id)
            if room is not None:
                rooms.append(room)
        return tuple(rooms)

    async def for_game(self, game_id: UUID) -> Conversation | None:
        """The room this game belongs to, **with its row locked**.

        Its one caller is the telling that writes the *played* line, which is a
        write — so this takes the lock the append needs, exactly as
        ``for_challenge`` does.
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
