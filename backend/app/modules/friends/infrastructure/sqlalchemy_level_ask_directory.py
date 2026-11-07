"""``LevelsAskedByTheReader``, ``AsksWaitingOnALevel`` and
``LevelAsksOfTheReader`` over ``friend_level_asks`` (#749, #764) — one table,
three ports, each handed to its own audience by the composition root.

The picker's *Asked* is one statement on the primary key's prefix, the asker and
an ``IN`` list of friends; the answer's lookup and the asks made of a reader are
one each on ``ix_friend_level_asks_friend_id_sport`` (the second on its
prefix). **Same session as the write**, so an ask a moment ago is read by the
read that follows it.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.stored_time import stored_instant
from app.kernel import Sport
from app.modules.friends.domain.ports import AskOfTheReader
from app.modules.friends.infrastructure.friendship_model import FriendLevelAskORM


class SqlAlchemyLevelAskDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def sports_asked_by(
        self, asker: UUID, *, among: Collection[UUID]
    ) -> Mapping[UUID, frozenset[Sport]]:
        wanted = sorted(set(among), key=str)
        if not wanted:
            return {}
        rows = await self._session.execute(
            select(FriendLevelAskORM.friend_id, FriendLevelAskORM.sport).where(
                FriendLevelAskORM.asker_id == asker,
                FriendLevelAskORM.friend_id.in_(wanted),
            )
        )
        asked: dict[UUID, set[Sport]] = {}
        for friend_id, sport in rows:
            asked.setdefault(friend_id, set()).add(Sport(sport))
        return {friend_id: frozenset(sports) for friend_id, sports in asked.items()}

    async def askers_waiting_on(self, friend: UUID, sport: Sport) -> tuple[UUID, ...]:
        askers = await self._session.scalars(
            select(FriendLevelAskORM.asker_id)
            .where(
                FriendLevelAskORM.friend_id == friend,
                FriendLevelAskORM.sport == sport.value,
                FriendLevelAskORM.got_at.is_(None),
            )
            .order_by(FriendLevelAskORM.asker_id)
        )
        return tuple(askers.all())

    async def asks_of(self, reader: UUID) -> tuple[AskOfTheReader, ...]:
        rows = await self._session.execute(
            select(
                FriendLevelAskORM.asker_id,
                FriendLevelAskORM.sport,
                FriendLevelAskORM.asked_at,
            ).where(
                FriendLevelAskORM.friend_id == reader,
                FriendLevelAskORM.got_at.is_(None),
                FriendLevelAskORM.set_aside_at.is_(None),
            )
        )
        return tuple(
            AskOfTheReader(
                asker_id=asker_id, sport=Sport(sport), asked_at=stored_instant(at)
            )
            for asker_id, sport, at in rows
        )
