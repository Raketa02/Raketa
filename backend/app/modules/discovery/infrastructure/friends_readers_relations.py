"""``ReadersRelations`` over Friends' own read of the reader's relations —
**signed here**, so the arrow runs ``discovery → friends`` and Friends imports
none of its readers (``.importlinter``): the round friend button on every
people card (``docs/adr/0204`` §9). Friends' spelling is translated into this
context's own, value for value."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.modules.discovery.domain.relation import Relation
from app.modules.friends.application.reads import ReadRelations


@final
class FriendsReadersRelations:
    def __init__(self, relations: ReadRelations) -> None:
        self._relations = relations

    async def relations_of(
        self, reader: UUID, players: Collection[UUID]
    ) -> Mapping[UUID, Relation]:
        return {
            player_id: Relation(relation.value)
            for player_id, relation in (
                await self._relations.relations_of(reader, players)
            ).items()
        }
