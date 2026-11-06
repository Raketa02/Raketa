"""``RelationsOfTheReader`` over Friends' published read — the reader's
relation to the person on the record (``docs/adr/0202`` §2), translated into
this context's words by value, deciding nothing."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.friends.application.reads import ReadRelations
from app.modules.player_record.domain.record import RecordRelation


@final
class FriendsRelationsOfTheReader:
    def __init__(self, relations: ReadRelations) -> None:
        self._relations = relations

    async def relation_to(self, *, reader_id: UUID, subject_id: UUID) -> RecordRelation:
        if reader_id == subject_id:
            return RecordRelation.NONE
        relations = await self._relations.relations_of(reader_id, [subject_id])
        return RecordRelation(relations[subject_id].value)
