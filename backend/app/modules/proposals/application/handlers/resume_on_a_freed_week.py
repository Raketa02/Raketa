"""The subscriber that brings a paused week back — see
``resume_paused_yeses.py``.

Three ways a booked game stops being a player's: **they left it** — their own
week has room — and **it was called off at its cut-off** (#544), or **its club
cancelled it** (#547) — everybody still in has room.
"""

from __future__ import annotations

from app.application.events import DeliveryContext
from app.kernel import instant
from app.modules.bookings.domain.events import (
    CalledOffAtCutOff,
    CancelledByClub,
    SeatLeft,
)
from app.modules.proposals.application.resume_paused_yeses import ResumePausedYeses


class ResumeYesesOnAFreedWeek:
    def __init__(self, resume: ResumePausedYeses) -> None:
        self._resume = resume

    async def __call__(
        self,
        event: SeatLeft | CalledOffAtCutOff | CancelledByClub,
        context: DeliveryContext,
    ) -> None:
        players = (
            (event.player_id,) if isinstance(event, SeatLeft) else event.player_ids
        )
        for player_id in players:
            await self._resume.execute(player_id, at=instant(event.occurred_at))
