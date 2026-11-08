"""``RelationsOfTheReader`` over Friends' published reads — the reader's
relation to the person on the record (``docs/adr/0202`` §2), and whether a
request from the reader would be admitted (``docs/adr/0203`` §9, #773) —
translated into this context's words by value, deciding nothing.

**Who may be asked is Friends' rule, asked here and never respelled**
(``WhoMayBeAsked``): the ask is admitted by the same object, so the record
cannot offer *Add friend* where a press would be refused, or hide it where one
would go through."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.friends.application.reads import ReadRelations
from app.modules.friends.application.requests import WhoMayBeAsked
from app.modules.player_record.domain.record import RecordRelation


@final
class FriendsRelationsOfTheReader:
    def __init__(self, relations: ReadRelations, who: WhoMayBeAsked) -> None:
        self._relations = relations
        self._who = who

    async def relation_to(self, *, reader_id: UUID, subject_id: UUID) -> RecordRelation:
        if reader_id == subject_id:
            return RecordRelation.NONE
        relations = await self._relations.relations_of(reader_id, [subject_id])
        return RecordRelation(relations[subject_id].value)

    async def may_ask(self, *, reader_id: UUID, subject_id: UUID, now: Instant) -> bool:
        if reader_id == subject_id:
            return False
        return await self._who.admits(reader_id, subject_id, now=now) is not None


__all__ = ["FriendsRelationsOfTheReader"]
