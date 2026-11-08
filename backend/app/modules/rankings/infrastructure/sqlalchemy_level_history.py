"""``LevelHistory`` over ``ranking_level_history`` (#769; ``docs/adr/0203`` §4).

**An append is written once per event.** The points a stream's fold makes are
compared with the ones already held for that player and sport — one statement
on the index's prefix — and only the new ones are inserted, with ``ON CONFLICT
DO NOTHING`` on the event so two deliveries at once still write each point
once. The mover hands it the whole stream's points, so a player whose earlier
points a store never had gains them on their next result.

**Each player's point at an instant is two statements**: the latest at or
before it for each player — a window over **every point of the sport up to the
instant**, partitioned by player along ``ix_ranking_level_history_points``,
whose rows past the players asked about are dropped here — then the first point
of whoever has none by then: only players whose rating opened since, every one
of them *New*. **General's chips no longer read it**: its pass reads the points
of the week's movers alone, beside the rows (#770, ``SqlAlchemyRankingRows``);
this is for a read over a few players. Both
dialects the backend runs on speak the window, SQLite since 3.25.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from itertools import groupby
from typing import Final
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.infrastructure.database.stored_time import stored_instant
from app.kernel import Instant, Sport
from app.modules.rankings.domain.ranking import LevelPoint
from app.modules.rankings.infrastructure.dialect_insert import insert_into
from app.modules.rankings.infrastructure.ranking_model import LevelPointORM

#: Points per insert: seven columns each, well inside every driver's limit on
#: bound parameters.
_CHUNK: Final = 100


class SqlAlchemyLevelHistory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, points: Sequence[LevelPoint]) -> int:
        def stream(point: LevelPoint) -> tuple[str, str]:
            return (str(point.player_id), point.sport.value)

        written = 0
        for _, one_stream in groupby(sorted(points, key=stream), key=stream):
            written += await self._append_stream(list(one_stream))
        return written

    async def _append_stream(self, points: list[LevelPoint]) -> int:
        first = points[0]
        held = set(
            await self._session.scalars(
                select(LevelPointORM.event_id).where(
                    LevelPointORM.sport == first.sport.value,
                    LevelPointORM.player_id == first.player_id,
                )
            )
        )
        new = [point for point in points if point.event_id not in held]
        for start in range(0, len(new), _CHUNK):
            await self._session.execute(
                insert_into(self._session, LevelPointORM)
                .values([_values(point) for point in new[start : start + _CHUNK]])
                .on_conflict_do_nothing(index_elements=[LevelPointORM.event_id])
            )
        return len(new)

    async def points_at(
        self, sport: Sport, at: Instant, player_ids: Collection[UUID]
    ) -> Mapping[UUID, LevelPoint]:
        wanted = set(player_ids)
        if not wanted:
            return {}
        by_then = await self._one_per_player(
            LevelPointORM.sport == sport.value,
            LevelPointORM.at <= at,
            latest_first=True,
        )
        found = {
            player_id: point
            for player_id, point in by_then.items()
            if player_id in wanted
        }
        since = wanted - found.keys()
        if since:
            first = await self._one_per_player(
                LevelPointORM.sport == sport.value,
                LevelPointORM.player_id.in_(sorted(since, key=str)),
                latest_first=False,
            )
            found.update(first)
        return found

    async def _one_per_player(
        self, *where: ColumnElement[bool], latest_first: bool
    ) -> dict[UUID, LevelPoint]:
        """One point per player among those ``where`` keeps: the latest (the
        most results breaking a tie of instants), or the first — the fewest
        results, which is the opening."""

        order = (
            (LevelPointORM.at.desc(), LevelPointORM.results.desc())
            if latest_first
            else (LevelPointORM.results, LevelPointORM.at)
        )
        numbered = (
            select(
                LevelPointORM,
                func.row_number()
                .over(partition_by=LevelPointORM.player_id, order_by=order)
                .label("nth"),
            )
            .where(*where)
            .subquery()
        )
        point = aliased(LevelPointORM, numbered)
        stored = await self._session.scalars(select(point).where(numbered.c.nth == 1))
        return {row.player_id: _point(row) for row in stored.all()}


def _values(point: LevelPoint) -> dict[str, object]:
    return {
        "event_id": point.event_id,
        "player_id": point.player_id,
        "sport": point.sport.value,
        "at": point.at,
        "hundredths": point.hundredths,
        "results": point.results,
        "level_reached_at": point.level_reached_at,
    }


def _point(stored: LevelPointORM) -> LevelPoint:
    return LevelPoint(
        event_id=stored.event_id,
        player_id=stored.player_id,
        sport=Sport(stored.sport),
        at=stored_instant(stored.at),
        hundredths=stored.hundredths,
        results=stored.results,
        level_reached_at=stored_instant(stored.level_reached_at),
    )
