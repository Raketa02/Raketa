"""The ranking's read in Proposals' words — **signed here**, so the arrow runs
``proposals → rankings`` and Rankings imports none of its readers
(``.importlinter``): Home's trophy, its General place and since #771 its
Friends place (#768; ``docs/adr/0203`` §5)."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.proposals.domain.ports import HomeRanking
from app.modules.rankings.application.reads import ReadHomeRanking


@final
class RankingsOnHome:
    def __init__(self, read: ReadHomeRanking) -> None:
        self._read = read

    async def of(self, reader: UUID) -> HomeRanking | None:
        ranking = await self._read.execute(reader)
        if ranking is None:
            return None
        return HomeRanking(
            sport=ranking.sport,
            general_place=ranking.general_place,
            friends_place=ranking.friends_place,
        )
