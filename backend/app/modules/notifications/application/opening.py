"""**Opening the recent notices** — the bell's number starts again from nought
(#621; the mechanics Q101; the screens A9).

The phone says so as the list behind the bell opens, on any phone: the moment
is recorded on the player's bell, with the newest notice the list held then,
and only what reaches the list after counts. **Idempotent, and never back**:
opened again at the same moment, or with a clock behind the last visit, it
records nothing.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.notifications.domain.ports import BellRepository


@final
class OpenRecentNotices:
    def __init__(self, *, bells: BellRepository, uow: UnitOfWork, clock: Clock) -> None:
        self._bells = bells
        self._uow = uow
        self._clock = clock

    async def execute(self, player_id: UUID) -> None:
        bell = await self._bells.load(player_id)
        if bell.open(at=instant(self._clock.now())) is None:
            return
        try:
            await self._bells.save(bell)
        except EventStreamVersionConflict:
            # Opened on another phone at the same moment: that visit stands.
            await self._uow.rollback()
            return
        await self._uow.commit()
