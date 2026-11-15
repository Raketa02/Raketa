"""The current levels' two writers: **the follower**, on every delivered
rating event that moves a Level, and **the rebuild**, over every rating
(``docs/adr/0204`` §10; #794).

**Both ask the rating the same question** — where does this player's rating in
this sport stand now (``LevelSources``) — and write the answer whole, as the
directory's writers do. So a redelivery writes the same entry, a delivery out
of order writes what the stream stands at, and the rebuild writes what live
delivery did; the store keeps the fold with the most results, so one read
before a later move committed never takes it back.

**No commit** in the follower: the transaction is the delivery's. The rebuild
commits once, in the run that rebuilds the directory beside it
(``infrastructure/rebuild_cli.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Sport
from app.modules.discovery.domain.ports import LevelSources, PlayerLevels


@final
class FollowTheLevels:
    """A Level opened or moved, so the player's entry in that sport is written
    again from where their rating stands."""

    def __init__(self, *, sources: LevelSources, levels: PlayerLevels) -> None:
        self._sources = sources
        self._levels = levels

    async def execute(self, player_id: UUID, sport: Sport) -> None:
        # A rating is never closed: a delivered event names a stream that
        # holds a level.
        level = await self._sources.level_of(player_id, sport)
        if level is not None:
            await self._levels.save(level)


@final
@dataclass(frozen=True, slots=True)
class LevelsRebuilt:
    #: Ratings the store holds, every one an entry.
    levels: int


@final
class RebuildTheLevels:
    """Every entry, written from every rating the event store holds — so the
    players rated before the projection shipped are compared. Running it twice
    changes nothing."""

    def __init__(
        self, *, sources: LevelSources, levels: PlayerLevels, uow: UnitOfWork
    ) -> None:
        self._sources = sources
        self._levels = levels
        self._uow = uow

    async def execute(self) -> LevelsRebuilt:
        written = 0
        for level in await self._sources.every_level():
            await self._levels.save(level)
            written += 1
        await self._uow.commit()
        return LevelsRebuilt(levels=written)
