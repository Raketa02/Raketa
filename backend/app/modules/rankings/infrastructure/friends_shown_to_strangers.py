"""Friends' ``ShownToStrangers`` over the Ranking's own read — **signed here**,
so the arrow runs ``rankings → friends`` and Friends imports none of its
readers (``.importlinter``): what admits a request from somebody the two share
no group with (#773; ``docs/adr/0203`` §9)."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.rankings.application.shown_on_general import ShownOnGeneral


@final
class RankingsShownToStrangers:
    def __init__(self, shown: ShownOnGeneral) -> None:
        self._shown = shown

    async def shown(self, player_id: UUID, *, now: Instant) -> bool:
        return await self._shown.shown(player_id, now=now)


__all__ = ["RankingsShownToStrangers"]
