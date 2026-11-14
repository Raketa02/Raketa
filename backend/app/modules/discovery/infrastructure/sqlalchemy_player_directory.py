"""``PlayerDirectory`` over ``discovery_players`` and ``discovery_player_tags``
(``docs/adr/0204`` §10).

**An entry is written whole**: the row upserted, the account's tags deleted and
written again, in the caller's transaction — so the tags are always the
profile's as the follower last read them, and a redelivery writes the same
rows. ``forget`` deletes both.

**Who may be on a row is one ``WHERE``**: named, playing, *Show me to new
people* on, joined after the instant, and none of the ids left out — the
reader and every block either way, tens at most, as one ``NOT IN``.
"""

from __future__ import annotations

from collections.abc import Collection
from datetime import timezone
from typing import final
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.stored_time import stored_instant
from app.kernel import Instant
from app.modules.discovery.domain.directory import DirectoryEntry
from app.modules.discovery.domain.new_in_raketa import Joiner
from app.modules.discovery.infrastructure.directory_model import (
    DirectoryPlayerORM,
    DirectoryTagORM,
)
from app.modules.discovery.infrastructure.dialect_insert import insert_into


@final
class SqlAlchemyPlayerDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, entry: DirectoryEntry) -> None:
        values = _values(entry)
        await self._session.execute(
            insert_into(self._session, DirectoryPlayerORM)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[DirectoryPlayerORM.player_id],
                set_={
                    name: value for name, value in values.items() if name != "player_id"
                },
            )
        )
        await self._session.execute(
            delete(DirectoryTagORM).where(DirectoryTagORM.player_id == entry.player_id)
        )
        tags = sorted(entry.player.tags) if entry.player is not None else []
        if tags:
            await self._session.execute(
                insert_into(self._session, DirectoryTagORM).values(
                    [{"player_id": entry.player_id, "tag": tag} for tag in tags]
                )
            )

    async def forget(self, player_id: UUID) -> None:
        await self._session.execute(
            delete(DirectoryTagORM).where(DirectoryTagORM.player_id == player_id)
        )
        await self._session.execute(
            delete(DirectoryPlayerORM).where(DirectoryPlayerORM.player_id == player_id)
        )

    async def who_joined(
        self,
        *,
        after: Instant,
        leaving_out: Collection[UUID],
        limit: int | None = None,
    ) -> tuple[Joiner, ...]:
        query = (
            select(
                DirectoryPlayerORM.player_id,
                DirectoryPlayerORM.nickname,
                DirectoryPlayerORM.photo_id,
                DirectoryPlayerORM.joined_at,
            )
            .where(
                DirectoryPlayerORM.plays.is_(True),
                DirectoryPlayerORM.open_to_new_people.is_(True),
                DirectoryPlayerORM.nickname.is_not(None),
                DirectoryPlayerORM.joined_at > after.astimezone(timezone.utc),
            )
            .order_by(DirectoryPlayerORM.joined_at.desc(), DirectoryPlayerORM.player_id)
        )
        if leaving_out:
            query = query.where(
                DirectoryPlayerORM.player_id.not_in(sorted(leaving_out, key=str))
            )
        if limit is not None:
            query = query.limit(limit)
        return tuple(
            Joiner(
                player_id=row.player_id,
                nickname=row.nickname,
                photo_id=row.photo_id,
                joined_at=stored_instant(row.joined_at),
            )
            for row in (await self._session.execute(query)).all()
        )


def _values(entry: DirectoryEntry) -> dict[str, object]:
    player = entry.player
    return {
        "player_id": entry.player_id,
        "nickname": entry.nickname,
        "plays": player is not None,
        "joined_at": None
        if player is None
        else player.joined_at.astimezone(timezone.utc),
        "photo_id": None if player is None else player.photo_id,
        "area_latitude": None
        if player is None or player.area is None
        else player.area.latitude,
        "area_longitude": None
        if player is None or player.area is None
        else player.area.longitude,
        "open_to_new_people": player is not None and player.open_to_new_people,
    }
