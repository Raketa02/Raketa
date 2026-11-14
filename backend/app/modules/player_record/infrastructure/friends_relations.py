"""Three readings of Friends' published relations, translated into this
context's words by value, deciding nothing: the reader's relation to the person
on the record (``docs/adr/0202`` §2), and two disclosures that keep a
switched-off player's record open to the reader (``docs/adr/0204`` §2) — **a
friendship**, and **a request they sent the reader** (a call made by #791)."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.friends.application.reads import ReadRelations
from app.modules.friends.domain.relation import FriendRelation
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


@final
class FriendsTheyAre:
    """``PriorDisclosure`` over Friends' own friend list. *We are friends.*

    A friendship as it stands, from the reader's side — an open request either
    way is not one — and **no block read**: a block ends a friendship, and the
    record's gates refuse a blocked pair whatever admitted them."""

    def __init__(self, relations: ReadRelations) -> None:
        self._relations = relations

    async def discloses(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        return subject_id in await self._relations.friends_among(
            reader_id, [subject_id]
        )


@final
class TheyAskedYou:
    """``PriorDisclosure`` over Friends' relations. *They asked me to be friends.*

    **A call made by #791**, beyond the spec's group, game and friendship: a
    switched-off player who sends a request has put themselves in front of the
    person they asked, so that person's Home card opens their record and *Add
    friend* there crosses the request — otherwise both would read *This record
    isn't available* about somebody waiting on them. Read from the reader's side
    (``ASKED_YOU``), so a request the reader never sees — asked across their
    block — discloses nothing, and one they sent the other way does not either."""

    def __init__(self, relations: ReadRelations) -> None:
        self._relations = relations

    async def discloses(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        if reader_id == subject_id:
            return False
        relations = await self._relations.relations_of(reader_id, [subject_id])
        return relations[subject_id] is FriendRelation.ASKED_YOU


__all__ = ["FriendsRelationsOfTheReader", "FriendsTheyAre", "TheyAskedYou"]
