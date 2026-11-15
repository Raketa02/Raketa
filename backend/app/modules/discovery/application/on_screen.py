"""**The on-screen report**, and what the two rows ask of its count
(``docs/adr/0204`` §7, §10, §12; the home-rows mechanics §9.2; #796).

The phone reports a row and the cards that came on screen in it. Each counts
**once per card, row and Warsaw day** (``rest``), and only for a player who may
be on a people row — never the reader, a block either way, a switched-off
player, an account that doesn't play or one that is gone, or an id nobody holds
— and **only while the two are unconnected**: a friend's day, or one while the
reader's request was open, never rests them later. Everything else asked about
is ignored, and the answer is the same.

**No event**: the count is the phone's word for what was seen, which no stream
holds and nothing is told (ADR-0204 §10). It commits on its own.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.discovery.domain.ports import (
    BlocksEitherWay,
    PlayerDirectory,
    ReadersRelations,
    RestCount,
)
from app.modules.discovery.domain.rest import (
    OnScreenRow,
    counts_toward_rest,
    day_on_screen,
    has_rested,
)


async def rested_among(
    rests: RestCount, reader: UUID, row: OnScreenRow, players: Collection[UUID]
) -> frozenset[UUID]:
    """Which of these have rested in the reader's row — what the two rows ask
    about the cards that could be fresh. Nothing is read for none."""

    if not players:
        return frozenset()
    days = await rests.days_on_screen(reader, row, players)
    return frozenset(player for player, seen in days.items() if has_rested(seen))


@final
class ReportOnScreen:
    """These cards came on screen in this row today."""

    def __init__(
        self,
        *,
        directory: PlayerDirectory,
        blocks: BlocksEitherWay,
        relations: ReadersRelations,
        rests: RestCount,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._blocks = blocks
        self._relations = relations
        self._rests = rests
        self._uow = uow
        self._clock = clock

    async def execute(
        self, reader: UUID, row: OnScreenRow, players: Collection[UUID]
    ) -> None:
        day = day_on_screen(self._clock.now())
        listed = await self._directory.which_may_be_listed(
            set(players), leaving_out={reader, *await self._blocks.either_way(reader)}
        )
        if not listed:
            return
        relations = await self._relations.relations_of(reader, listed)
        unconnected = [one for one in listed if counts_toward_rest(relations[one])]
        if not unconnected:
            return
        await self._rests.came_on_screen(reader, row, unconnected, day=day)
        await self._uow.commit()
