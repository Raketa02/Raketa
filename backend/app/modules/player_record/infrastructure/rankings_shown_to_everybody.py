"""``ShownToEverybody`` over the Ranking's own read — the record's fourth strand
(``docs/adr/0203`` §9, #773): listed on General in a sport and *Show me in
General* on, translated into this context's words, deciding nothing. **Signed
here**, so the arrow runs ``player_record → rankings`` and the Ranking imports
none of its readers (``.importlinter``)."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.rankings.application.shown_on_general import ShownOnGeneral


@final
class RankingsShownToEverybody:
    def __init__(self, shown: ShownOnGeneral) -> None:
        self._shown = shown

    async def shows(self, subject_id: UUID, *, now: Instant) -> bool:
        return await self._shown.shown(subject_id, now=now)


__all__ = ["RankingsShownToEverybody"]
