"""Friends' reads in Proposals' words — **signed here**, so the arrow runs
``proposals → friends`` and Friends imports none of its readers
(``.importlinter``): the reader's relations a face is tagged with, the friend
requests on Home (``docs/adr/0202`` §1–§2), and the asks for a level on Home
(§4's 2026-11-07 amendment, #764).

**A request from *Same competitive level* reads today's % even** (#794;
``docs/adr/0204`` §9, call 6): the reader and the requester, one a side, through
``BalanceForecasts`` — the deck's own forecast port, the one forecast function
— so the card says *91% even* as the row did, and nothing when either no
longer holds a level in the sport. **And a request from *Same vibe* counts
today's tags in common** (#795), through ``TagsInCommon``: *6 things in
common*, or none once they share none. **Every request names the requester's
Level in every sport they hold one in** (#814): Friends' card carries them,
read for every requester in one batch."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.kernel import Sport
from app.modules.friends.application.reads import (
    ReadLevelAsksOnHome,
    ReadRelations,
    ReadRequestsOnHome,
    RequestOnHome,
)
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin
from app.modules.proposals.domain.deck import Sides
from app.modules.proposals.domain.ports import (
    BalanceForecasts,
    HomeFriendRequest,
    HomeLevelAsk,
    HomeLevelAsker,
    HomeRequestLevel,
    TagsInCommon,
)


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
    def __init__(
        self,
        requests: ReadRequestsOnHome,
        *,
        forecasts: BalanceForecasts,
        tags: TagsInCommon,
    ) -> None:
        self._requests = requests
        self._forecasts = forecasts
        self._tags = tags

    async def of(self, reader: UUID) -> tuple[HomeFriendRequest, ...]:
        cards = await self._requests.execute(reader)
        evens = await self._evens(reader, cards)
        in_common = await self._tags.in_common(
            reader,
            [
                card.requester_id
                for card in cards
                if card.where.made_from is RequestOrigin.SAME_VIBE
            ],
        )
        return tuple(
            HomeFriendRequest(
                requester_id=card.requester_id,
                nickname=card.nickname,
                photo_id=card.photo_id,
                photo_url=card.photo_url,
                asked_at=card.asked_at,
                by_link=card.where.made_from is RequestOrigin.LINK,
                from_ranking=card.where.made_from is RequestOrigin.RANKING,
                from_new_players=card.where.made_from is RequestOrigin.NEW_PLAYERS,
                from_same_level=card.where.made_from is RequestOrigin.SAME_LEVEL,
                from_same_vibe=card.where.made_from is RequestOrigin.SAME_VIBE,
                group_id=None if card.group is None else card.group.group_id,
                group_name=None if card.group is None else card.group.name,
                sport=card.where.sport,
                level=card.level,
                reliability_points=card.reliability.points,
                reliability_band=card.reliability.band,
                percent_even=evens.get(card.requester_id),
                in_common=in_common.get(card.requester_id),
                levels=tuple(
                    HomeRequestLevel(sport=one.sport, level=one.level)
                    for one in card.levels
                ),
            )
            for card in cards
        )

    async def _evens(
        self, reader: UUID, cards: tuple[RequestOnHome, ...]
    ) -> dict[UUID, int]:
        """Today's % even for each request from *Same competitive level*, one
        forecast read per sport — absent where either holds no level."""

        by_sport: dict[Sport, list[UUID]] = {}
        for card in cards:
            if card.where.made_from is RequestOrigin.SAME_LEVEL and card.where.sport:
                by_sport.setdefault(card.where.sport, []).append(card.requester_id)
        evens: dict[UUID, int] = {}
        for sport, requesters in by_sport.items():
            forecasts = await self._forecasts.forecasts(
                [Sides(yours=(reader,), theirs=(one,)) for one in requesters],
                sport=sport,
            )
            for requester, forecast in zip(requesters, forecasts, strict=True):
                if forecast is not None:
                    evens[requester] = forecast.pct
        return evens


@final
class FriendsLevelAsksOnHome:
    def __init__(self, asks: ReadLevelAsksOnHome) -> None:
        self._asks = asks

    async def of(self, reader: UUID) -> tuple[HomeLevelAsk, ...]:
        return tuple(
            HomeLevelAsk(
                sport=card.sport,
                askers=tuple(
                    HomeLevelAsker(
                        player_id=asker.player_id,
                        nickname=asker.nickname,
                        photo_id=asker.photo_id,
                        photo_url=asker.photo_url,
                    )
                    for asker in card.askers
                ),
            )
            for card in await self._asks.execute(reader)
        )
