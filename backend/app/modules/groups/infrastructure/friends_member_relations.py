"""``MemberRelations`` — the reader's relation to each member on a Members list,
lent by Friends (``docs/adr/0202`` §2) and signed here over its published read,
so the arrow runs ``groups → friends``."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from app.modules.friends.application.reads import ReadRelations
from app.modules.friends.domain.relation import FriendRelation


class FriendsMemberRelations:
    def __init__(self, relations: ReadRelations) -> None:
        self._relations = relations

    async def relations_of(
        self, reader: UUID, players: Collection[UUID]
    ) -> Mapping[UUID, FriendRelation]:
        return await self._relations.relations_of(reader, players)
