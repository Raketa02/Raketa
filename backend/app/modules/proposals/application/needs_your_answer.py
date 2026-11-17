"""**Closing Needs your answer** — the envelope's badge starts again from nought
(#815; ``docs/adr/0205`` §3).

The phone says so whenever the sheet goes away for good — ✕, a swipe down, a
tap outside it, the last answer, a screen it hands over to — and sends back
**the watermark of the read the sheet showed**: Home's ``needs_your_answer``,
the newest arrival it held. Only what arrived after that is new, on every
phone. **Never the moment of the close**, so an item that reached the server
between the phone's read and its close stays new. A read with nothing waiting
serves no watermark, and closing on it records nothing.

**Idempotent, and never back**: the same watermark again, or an older one — a
phone closing on an older read after another phone closed on a newer one —
records nothing. **Two phones closing at once** collide on the stream: the one
that lost reads the other's visit and closes **once more**, so the newer of
the two watermarks is the one kept, whichever landed first. A third collision
in a row is let go: its close stands.
"""

from __future__ import annotations

from typing import Final, final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.proposals.domain.ports import NeedsYourAnswerVisits

#: A close and the one more it makes after losing a collision.
_TRIES: Final = 2


@final
class CloseNeedsYourAnswer:
    def __init__(
        self, *, visits: NeedsYourAnswerVisits, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._visits = visits
        self._uow = uow
        self._clock = clock

    async def execute(self, player_id: UUID, *, watermark: Instant | None) -> None:
        if watermark is None:
            return
        for _ in range(_TRIES):
            visit = await self._visits.load(player_id)
            if visit.close(watermark=watermark, at=instant(self._clock.now())) is None:
                return
            try:
                await self._visits.save(visit)
            except EventStreamVersionConflict:
                # Closed on another phone a moment before: read its visit.
                await self._uow.rollback()
                continue
            await self._uow.commit()
            return
