"""``RankingRows`` over ``ranking_rows``.

**A sport's listed rows are one statement** (#770), read in place order,
**each joined to its player's level-history point at the chip's instant** —
**for a player whose last result settled after it**. Their points are numbered
per player — the latest at or before the instant first (most results breaking
a tie of instants), else the fewest results first, which is the opening — and
the first kept. **A player with no result since stood then where they stand
now**, so their history is never read: at 50,000 listed players that is the
difference between sorting every point of the sport and sorting the week's
(the Rankings rule note has the numbers and the plans). So the order, every
place and every chip are worked out from one reading. **Columns, never ORM
objects**: a pass hands back every listed row, and hydrating fifty thousand
entities twice over was most of what it cost. Both dialects the backend runs
on speak the window, SQLite since 3.25. **A reader's Friends table is the same
statement over the reader and their friends alone** (#771), so it is worked
out on each read from one reading too. A player's own rows are one statement
on the primary key's prefix. **Same
session as the write**, so a row folded a moment ago is read by the read that
follows it in the transaction. The upsert is a statement, never an ORM object,
so every read refreshes what the session already holds (``populate_existing``).

**A save is one conditional upsert**, ``INSERT … ON CONFLICT DO UPDATE … WHERE
stored.results <= new.results``, so *never replaced by a row with fewer
results* holds under two deliveries at once: Postgres locks the conflicting row
and evaluates the condition against what the other committed. Both dialects the
backend runs on speak the same clause, SQLite since 3.24.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Final
from uuid import UUID

from sqlalchemy import Row, and_, case, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.stored_time import (
    stored_instant,
    stored_instant_or_none,
)
from app.kernel import Instant, Sport
from app.modules.rankings.domain.general_order import ListedAndThen
from app.modules.rankings.domain.ranking import (
    LevelPoint,
    Outcome,
    RankingRow,
    marks_of,
)
from app.modules.rankings.infrastructure.dialect_insert import insert_into
from app.modules.rankings.infrastructure.ranking_model import (
    LevelPointORM,
    RankingRowORM,
)

#: The columns a newer fold rewrites — everything but the key.
_FOLDED: Final = (
    "hundredths",
    "sigma",
    "results",
    "last_result_at",
    "level_reached_at",
    "general_entered_at",
    "friends_entered_at",
    "form",
)


class SqlAlchemyRankingRows:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, row: RankingRow) -> None:
        statement = insert_into(self._session, RankingRowORM).values(
            player_id=row.player_id,
            sport=row.sport.value,
            hundredths=row.hundredths,
            sigma=row.sigma,
            results=row.results,
            last_result_at=row.last_result_at,
            level_reached_at=row.level_reached_at,
            general_entered_at=row.general_entered_at,
            friends_entered_at=row.friends_entered_at,
            form=marks_of(row.form),
        )
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[RankingRowORM.player_id, RankingRowORM.sport],
                set_={column: statement.excluded[column] for column in _FOLDED},
                where=RankingRowORM.results <= statement.excluded.results,
            )
        )

    async def of_player(self, player_id: UUID) -> tuple[RankingRow, ...]:
        rows = await self._session.scalars(
            select(RankingRowORM)
            .where(RankingRowORM.player_id == player_id)
            .order_by(RankingRowORM.sport)
            .execution_options(populate_existing=True)
        )
        return tuple(_row(stored) for stored in rows.all())

    async def listed(
        self,
        sport: Sport,
        *,
        at_least: int,
        since: Instant,
        then: Instant,
        among: Collection[UUID] | None = None,
    ) -> tuple[ListedAndThen, ...]:
        if among is not None and not among:
            return ()
        rows, points = RankingRowORM.__table__, LevelPointORM.__table__
        listed = (
            select(*(rows.c[column] for column in _LISTED))
            .where(
                rows.c.sport == sport.value,
                rows.c.results >= at_least,
                rows.c.last_result_at > since,
                *(
                    ()
                    if among is None
                    else (rows.c.player_id.in_(sorted(set(among), key=str)),)
                ),
            )
            .cte("listed")
        )
        by_then = points.c.at <= then
        numbered = (
            select(
                *(points.c[column] for column in _POINT),
                func.row_number()
                .over(
                    partition_by=points.c.player_id,
                    order_by=(
                        # The points by then first, the latest of them first...
                        case((by_then, literal(0)), else_=literal(1)),
                        case((by_then, points.c.at)).desc(),
                        case((by_then, -points.c.results), else_=points.c.results),
                        # ...and with none by then, the fewest results first.
                        points.c.at,
                    ),
                )
                .label("nth"),
            )
            .select_from(
                listed.join(
                    points,
                    and_(
                        points.c.sport == sport.value,
                        points.c.player_id == listed.c.player_id,
                    ),
                )
            )
            # Only who moved since then: everybody else stood then as now.
            .where(listed.c.last_result_at > then)
            .subquery("numbered")
        )
        read = await self._session.execute(
            select(
                *(listed.c[column] for column in _LISTED),
                *(numbered.c[column].label(f"then_{column}") for column in _POINT),
            )
            .select_from(
                listed.outerjoin(
                    numbered,
                    and_(
                        numbered.c.player_id == listed.c.player_id,
                        numbered.c.nth == 1,
                    ),
                )
            )
            .order_by(
                listed.c.hundredths.desc(),
                listed.c.results.desc(),
                listed.c.level_reached_at,
                listed.c.player_id,
            )
        )
        return tuple(_listed_and_then(sport, found) for found in read.all())


#: The columns a pass reads of a row and of its point — never the ORM objects.
_LISTED: Final = (
    "player_id",
    "hundredths",
    "sigma",
    "results",
    "last_result_at",
    "level_reached_at",
    "general_entered_at",
    "friends_entered_at",
    "form",
)
_POINT: Final = (
    "event_id",
    "player_id",
    "at",
    "hundredths",
    "results",
    "level_reached_at",
)


def _listed_and_then(sport: Sport, found: Row[tuple[object, ...]]) -> ListedAndThen:
    read = found._mapping
    row = RankingRow(
        player_id=read["player_id"],
        sport=sport,
        hundredths=read["hundredths"],
        sigma=read["sigma"],
        results=read["results"],
        last_result_at=stored_instant(read["last_result_at"]),
        level_reached_at=stored_instant(read["level_reached_at"]),
        general_entered_at=stored_instant_or_none(read["general_entered_at"]),
        friends_entered_at=stored_instant(read["friends_entered_at"]),
        form=Outcome.of_marks(read["form"]),
    )
    if read["then_event_id"] is None:
        return ListedAndThen(row=row, then=None)
    return ListedAndThen(
        row=row,
        then=LevelPoint(
            event_id=read["then_event_id"],
            player_id=read["then_player_id"],
            sport=sport,
            at=stored_instant(read["then_at"]),
            hundredths=read["then_hundredths"],
            results=read["then_results"],
            level_reached_at=stored_instant(read["then_level_reached_at"]),
        ),
    )


def _row(stored: RankingRowORM) -> RankingRow:
    return RankingRow(
        player_id=stored.player_id,
        sport=Sport(stored.sport),
        hundredths=stored.hundredths,
        sigma=stored.sigma,
        results=stored.results,
        last_result_at=stored_instant(stored.last_result_at),
        level_reached_at=stored_instant(stored.level_reached_at),
        general_entered_at=stored_instant_or_none(stored.general_entered_at),
        friends_entered_at=stored_instant(stored.friends_entered_at),
        form=Outcome.of_marks(stored.form),
    )
