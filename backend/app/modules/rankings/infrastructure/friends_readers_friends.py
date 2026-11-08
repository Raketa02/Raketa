"""``ReadersFriends`` over Friends' own read of the reader's relations — **signed
here**, so the arrow runs ``rankings → friends`` and Friends imports none of its
readers (``.importlinter``): the friend list the Friends view is worked out over
(#771; ``docs/adr/0203`` §3, §10)."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.friends.application.reads import ReadRelations


@final
class FriendsReadersFriends:
    def __init__(self, relations: ReadRelations) -> None:
        self._relations = relations

    async def friends_of(self, reader: UUID) -> frozenset[UUID]:
        return await self._relations.friends_of(reader)
