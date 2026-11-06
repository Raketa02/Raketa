"""Friends' reads in Proposals' words — **signed here**, so the arrow runs
``proposals → friends`` and Friends imports none of its readers
(``.importlinter``): the reader's relations a face is tagged with, and the
friend requests on Home (``docs/adr/0202`` §1–§2)."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.modules.friends.application.reads import ReadRelations, ReadRequestsOnHome
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin
from app.modules.proposals.domain.ports import HomeFriendRequest


@final
class FriendsReaderRelations:
    def __init__(self, relations: ReadRelations) -> None:
        self._relations = relations

    async def friends_among(
        self, reader: UUID, players: Collection[UUID]
    ) -> frozenset[UUID]:
        return await self._relations.friends_among(reader, players)

    async def relations_of(
        self, reader: UUID, players: Collection[UUID]
    ) -> Mapping[UUID, FriendRelation]:
        return await self._relations.relations_of(reader, players)


@final
class FriendsRequestsOnHome:
    def __init__(self, requests: ReadRequestsOnHome) -> None:
        self._requests = requests

    async def of(self, reader: UUID) -> tuple[HomeFriendRequest, ...]:
        return tuple(
            HomeFriendRequest(
                requester_id=card.requester_id,
                nickname=card.nickname,
                photo_id=card.photo_id,
                photo_url=card.photo_url,
                asked_at=card.asked_at,
                by_link=card.where.made_from is RequestOrigin.LINK,
                group_id=None if card.group is None else card.group.group_id,
                group_name=None if card.group is None else card.group.name,
                sport=card.where.sport,
                level=card.level,
                reliability_points=card.reliability.points,
                reliability_band=card.reliability.band,
            )
            for card in await self._requests.execute(reader)
        )
