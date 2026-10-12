"""What passes from a booked game's ordinary Game to its booking after the
fill, over the one arrow ``bookings → games`` (#547).

``GameNoShowsOnTheRecord`` **answers this context's own demand** ``GameNoShows``
over the Games context's repository: who **Didn't come**, for good — caught at
the court, their late claim's day over unconfirmed (#657) — folded by the Game's
own rule, so *keeps plans* breaks a booked game on the record of somebody who
did not come, and never re-decides it here.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.games.domain.ports import GameRepository


@final
class GameNoShowsOnTheRecord:
    """``GameNoShows`` over the Games context's own aggregate."""

    def __init__(self, games: GameRepository) -> None:
        self._games = games

    async def did_not_come(self, booking_id: UUID, *, now: Instant) -> frozenset[UUID]:
        game = await self._games.for_challenge(booking_id)
        return frozenset() if game is None else game.didnt_come_at(now)
