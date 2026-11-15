"""``RestCount`` over ``discovery_rest_counts`` (``docs/adr/0204`` §10; #796).

**A report is one statement**: ``INSERT … ON CONFLICT DO UPDATE SET days =
days + 1 … WHERE stored.last_day < new.last_day`` — the first day inserts one,
a later day adds one, and the same day again changes nothing, under two
reports at once too, since the conflict is settled on the row. The ids come
sorted, so two reports naming the same cards lock them in one order.

**A row's read is one statement** per batch: the viewer, the row and the
batch's ids, by the key.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import date
from typing import final
from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.discovery.domain.rest import OnScreenRow
from app.modules.discovery.infrastructure.dialect_insert import insert_into
from app.modules.discovery.infrastructure.rest_count_model import (
    DiscoveryRestCountORM,
)


@final
class SqlAlchemyRestCount:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def came_on_screen(
        self,
        viewer: UUID,
        row: OnScreenRow,
        players: Collection[UUID],
        *,
        day: date,
    ) -> None:
        if not players:
            return
        statement = insert_into(self._session, DiscoveryRestCountORM).values(
            [
                {
                    "viewer_id": viewer,
                    "row": row.value,
                    "player_id": player,
                    "days": 1,
                    "last_day": day,
                }
                for player in sorted(set(players), key=str)
            ]
        )
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[
                    DiscoveryRestCountORM.viewer_id,
                    DiscoveryRestCountORM.row,
                    DiscoveryRestCountORM.player_id,
                ],
                set_={
                    "days": DiscoveryRestCountORM.days + 1,
                    "last_day": statement.excluded.last_day,
                },
                where=DiscoveryRestCountORM.last_day < statement.excluded.last_day,
            )
        )

    async def days_on_screen(
        self, viewer: UUID, row: OnScreenRow, players: Collection[UUID]
    ) -> Mapping[UUID, int]:
        if not players:
            return {}
        found = await self._session.execute(
            select(DiscoveryRestCountORM.player_id, DiscoveryRestCountORM.days).where(
                DiscoveryRestCountORM.viewer_id == viewer,
                DiscoveryRestCountORM.row == row.value,
                DiscoveryRestCountORM.player_id.in_(sorted(set(players), key=str)),
            )
        )
        return {player: days for player, days in found.all()}

    async def forget(self, player_id: UUID) -> None:
        await self._session.execute(
            delete(DiscoveryRestCountORM).where(
                or_(
                    DiscoveryRestCountORM.viewer_id == player_id,
                    DiscoveryRestCountORM.player_id == player_id,
                )
            )
        )
