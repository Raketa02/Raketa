"""The two card fields the index does not hold, read in two queries.

**A nickname comes from ``users``, which the index does not tail at all**, and a
photo id comes from the profile stream, which the index deliberately does not
project — ``candidate_projection`` refuses ``player_profile.photos_changed`` by
name, because the card is assembled outside the engine.

**Two queries for the whole shortlist, never a query per row.** This runs after
the floor, so it is at most twenty players even when the pool is five hundred.

**It reads the log rather than replaying twenty aggregates.** Loading each
profile would be twenty stream reads to answer one question about the last event
of each — and the question is genuinely about the latest value of one field, not
about the aggregate. So the photo read is one query over the two contracts that
carry a whole photo list, taking the last of them per stream. That is a read
model in everything but name, and the day it needs an index it gets one; the
alternative today is twenty replays on the live search path.

**A URL is never minted here.** ``docs/adr/0107``: photos are served through
short-lived presigned links and a search record is kept for ever, so what travels
is the id. The link is the client's next request.
"""

from __future__ import annotations

from typing import Collection, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.matchmaking.domain.cards import CardIdentity
from app.modules.player_profile.infrastructure.event_sourced_player_profile_repository import (  # noqa: E501
    PLAYER_PROFILE_AGGREGATE,
)
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM

#: The two contracts that carry a whole photo list. Both are *whole new value*
#: events — the projection rule the index is built on — so the last one on a
#: stream is the player's current list, and no earlier row has to be folded.
_PHOTO_CONTRACTS = (
    "player_profile.created",
    "player_profile.photos_changed",
)


class PlayerCardIdentities:
    """``PlayerCardSource`` over ``users`` and the profile streams."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def identities_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, CardIdentity]:
        """Each of these players' nickname and first photo.

        A player ``users`` has never heard of is **absent from the answer**
        rather than present with a blank name: a card with no nickname is not a
        card, and the caller drops the row before the record is written so that
        ``n_returned`` and the rows stored still agree.
        """

        if not player_ids:
            return {}
        wanted = list(player_ids)
        photos = await self._photos(wanted)
        nicknames = await self._session.execute(
            select(UserORM.id, UserORM.nickname).where(UserORM.id.in_(wanted))
        )
        return {
            player_id: CardIdentity(
                nickname=nickname, photo_id=photos.get(player_id)
            )
            for player_id, nickname in nicknames.all()
        }

    async def _photos(self, player_ids: list[UUID]) -> dict[UUID, UUID]:
        """The first photo id per player, from the latest list each published.

        Ordered by ``sequence_no`` — the store's only total order — and the last
        row per stream wins, which is the same rule the index's own tail applies
        and for the same reason: a position is the log's order, and
        ``occurred_at`` is not.
        """

        rows = await self._session.execute(
            select(EventStoreORM.aggregate_id, EventStoreORM.payload)
            .where(
                EventStoreORM.aggregate_type == PLAYER_PROFILE_AGGREGATE,
                EventStoreORM.aggregate_id.in_(player_ids),
                EventStoreORM.event_type.in_(_PHOTO_CONTRACTS),
            )
            .order_by(EventStoreORM.sequence_no)
        )
        latest: dict[UUID, UUID] = {}
        for player_id, payload in rows.all():
            ids = payload.get("photo_ids") or ()
            if ids:
                latest[player_id] = UUID(str(ids[0]))
            else:
                latest.pop(player_id, None)
        return latest
