"""The projection's three writers: **the move**, on every delivered
``rating.moved_on_result``; **the switch**, on every delivered
``player_profile.ranking_visibility_set`` (#772); and **the rebuild**, over
every rating stream (``docs/adr/0203`` §10). The move and the rebuild write
the row and the level history together.

**The switch is read live, never off the event**: the follower asks the
profile for its *Show me in General* and the version it stands at, and the
rows follow it, a switch read at an older version never replacing a newer
one — so two turns delivered in either order, or one delivered twice, leave
the latest. It forgets the kept order of every sport the player has a row
in, so the next read leaves them out, or puts them back.

**Both fold the whole stream**, through the one ``row_of`` and the one
``points_of``. So a redelivery folds the same stream to the same row and the
same points and changes nothing, a delivery that arrives out of order still
writes the row the stream stands at, and the rebuild produces what live
delivery did, row for row and point for point. **The history is handed every
point of the stream**, keyed by the event, so a point already held is left
alone and one a store never had is filled on the player's next result. Nothing
here keeps a cursor: the rating streams are the record, as they are for the
rating's own catch-up (``docs/adr/0139``).

**Each forgets its sport's kept General order** (#770), so the next read
works it out again and a result settling is reflected on it. The forget is the
delivery's last act before its commit, so a read that worked the order out in
between keeps what it read for at most the minute; one that misses a reader
the projection lists is worked out again (``TheGeneralOrder``).

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
from app.modules.player_profile.domain.events import RankingVisibilitySet
from app.modules.rankings.domain.ports import (
    GeneralOrders,
    GeneralSwitches,
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
    history gains the result's point — and the sport's kept order is
    forgotten."""

    def __init__(
        self,
        *,
        histories: RatingHistories,
        rows: RankingRows,
        level_history: LevelHistory,
        orders: GeneralOrders,
    ) -> None:
        self._histories = histories
        self._rows = rows
        self._level_history = level_history
        self._orders = orders

    async def __call__(
        self, event: RatingMovedOnResult, context: DeliveryContext
    ) -> None:
        history = await self._histories.history_of(event.player_id, Sport(event.sport))
        row = None if history is None else row_of(history)
        if history is not None and row is not None:
            await self._rows.save(row)
            await self._level_history.append(points_of(history))
            await self._orders.forget(row.sport)


@final
class FollowTheSwitch:
    """A player turned *Show me in General*, so their rows follow it — every
    sport, one they have no row in yet included — and the kept order of each
    sport they have a row in is forgotten."""

    def __init__(
        self,
        *,
        switches: GeneralSwitches,
        rows: RankingRows,
        orders: GeneralOrders,
    ) -> None:
        self._switches = switches
        self._rows = rows
        self._orders = orders

    async def __call__(
        self, event: RankingVisibilitySet, context: DeliveryContext
    ) -> None:
        switch = await self._switches.switch_of(event.player_id)
        if switch is None:
            return
        await self._rows.follow(switch)
        for row in await self._rows.of_player(event.player_id):
            await self._orders.forget(row.sport)


@final
@dataclass(frozen=True, slots=True)
class Rebuilt:
    #: Rating streams read.
    ratings: int
    #: Rows written: the ratings a result has moved.
    rows: int
    #: Level-history points the store didn't hold yet.
    points: int
    #: Profiles whose *Show me in General* the rows were made to follow.
    switches: int


@final
class RebuildTheRankings:
    """Every row and every level-history point, folded from every rating
    stream the event store holds — so the players who played before the
    ranking shipped are on it, and their chips read a real week — **and every
    profile's *Show me in General***, a player with no rating yet included
    (#772), so a projection rebuilt from nothing never lists a hidden player,
    now or after their first results. Running it twice changes nothing."""

    def __init__(
        self,
        *,
        histories: RatingHistories,
        rows: RankingRows,
        level_history: LevelHistory,
        switches: GeneralSwitches,
        orders: GeneralOrders,
        uow: UnitOfWork,
    ) -> None:
        self._histories = histories
        self._rows = rows
        self._level_history = level_history
        self._switches = switches
        self._orders = orders
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
        switches = await self._switches.every_switch()
        for switch in switches:
            await self._rows.follow(switch)
        await self._uow.commit()
        for sport in Sport:
            await self._orders.forget(sport)
        return Rebuilt(
            ratings=ratings, rows=written, points=points, switches=len(switches)
        )
