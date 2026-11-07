"""``RankingRows`` over ``ranking_rows``.

**A sport's listed rows are one statement on ``ix_ranking_rows_order``**, read
in place order; a player's own rows one on the primary key's prefix. **Same
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

from typing import Final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.stored_time import (
    stored_instant,
    stored_instant_or_none,
)
from app.kernel import Instant, Sport
from app.modules.rankings.domain.ranking import Outcome, RankingRow
from app.modules.rankings.infrastructure.dialect_insert import insert_into
from app.modules.rankings.infrastructure.ranking_model import RankingRowORM

#: A result in the stored form: ``W`` or ``L``, five at most.
_MARKS: Final = {Outcome.WIN: "W", Outcome.LOSS: "L"}
_OUTCOMES: Final = {mark: outcome for outcome, mark in _MARKS.items()}

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
            form="".join(_MARKS[outcome] for outcome in row.form),
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
        self, sport: Sport, *, at_least: int, since: Instant
    ) -> tuple[RankingRow, ...]:
        rows = await self._session.scalars(
            select(RankingRowORM)
            .where(
                RankingRowORM.sport == sport.value,
                RankingRowORM.results >= at_least,
                RankingRowORM.last_result_at > since,
            )
            .order_by(
                RankingRowORM.hundredths.desc(),
                RankingRowORM.results.desc(),
                RankingRowORM.level_reached_at,
                RankingRowORM.player_id,
            )
            .execution_options(populate_existing=True)
        )
        return tuple(_row(stored) for stored in rows.all())


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
        form=tuple(_OUTCOMES[mark] for mark in stored.form),
    )
