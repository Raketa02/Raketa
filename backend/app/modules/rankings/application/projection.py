"""The projection's two writers: **the move**, on every delivered
``rating.moved_on_result``, and **the rebuild**, over every rating stream
(``docs/adr/0203`` §10). Each writes the row and the level history together.

**Both fold the whole stream**, through the one ``row_of`` and the one
``points_of``. So a redelivery folds the same stream to the same row and the
same points and changes nothing, a delivery that arrives out of order still
writes the row the stream stands at, and the rebuild produces what live
delivery did, row for row and point for point. **The history is handed every
point of the stream**, keyed by the event, so a point already held is left
alone and one a store never had is filled on the player's next result. Nothing
here keeps a cursor: the rating streams are the record, as they are for the
rating's own catch-up (``docs/adr/0139``).

**No commit** in the move: the transaction is the delivery's. The rebuild is a
command-line run of its own and commits once at the end
(``infrastructure/rebuild_cli.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.application.events import DeliveryContext
from app.application.ports import UnitOfWork
from app.kernel import Sport
from app.modules.rankings.domain.ports import (
    LevelHistory,
    RankingRows,
    RatingHistories,
)
from app.modules.rankings.domain.ranking import points_of, row_of
from app.modules.rating.domain.events import RatingMovedOnResult


@final
class MoveTheRanking:
    """A result moved a Level, so the player's row in that sport is folded
    again from their rating stream — made on the first result — and the level
    history gains the result's point."""

    def __init__(
        self,
        *,
        histories: RatingHistories,
        rows: RankingRows,
        level_history: LevelHistory,
    ) -> None:
        self._histories = histories
        self._rows = rows
        self._level_history = level_history

    async def __call__(
        self, event: RatingMovedOnResult, context: DeliveryContext
    ) -> None:
        history = await self._histories.history_of(event.player_id, Sport(event.sport))
        row = None if history is None else row_of(history)
        if history is not None and row is not None:
            await self._rows.save(row)
            await self._level_history.append(points_of(history))


@final
@dataclass(frozen=True, slots=True)
class Rebuilt:
    #: Rating streams read.
    ratings: int
    #: Rows written: the ratings a result has moved.
    rows: int
    #: Level-history points the store didn't hold yet.
    points: int


@final
class RebuildTheRankings:
    """Every row and every level-history point, folded from every rating
    stream the event store holds — so the players who played before the
    ranking shipped are on it, and their chips read a real week. Running it
    twice changes nothing."""

    def __init__(
        self,
        *,
        histories: RatingHistories,
        rows: RankingRows,
        level_history: LevelHistory,
        uow: UnitOfWork,
    ) -> None:
        self._histories = histories
        self._rows = rows
        self._level_history = level_history
        self._uow = uow

    async def execute(self) -> Rebuilt:
        ratings = 0
        written = 0
        points = 0
        for history in await self._histories.every_history():
            ratings += 1
            row = row_of(history)
            if row is not None:
                await self._rows.save(row)
                written += 1
                points += await self._level_history.append(points_of(history))
        await self._uow.commit()
        return Rebuilt(ratings=ratings, rows=written, points=points)
