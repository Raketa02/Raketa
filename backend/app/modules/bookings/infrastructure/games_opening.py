"""``GameOpening`` over the Games context's own use case — the one a completed
line-up opens a game with, so a booked game is **an ordinary Game**, opened
exactly as one is today (``docs/adr/0189`` §5, Q6). The arrow runs
``bookings → games``; ``games`` does not know a booking exists, and reads the
booking's id where a line-up's game reads its challenge's: the arrangement it
came from.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant, Sport, invariant
from app.modules.games.application.commands import OpenPlannedGameCommand
from app.modules.games.application.open_planned_game import OpenPlannedGame
from app.modules.games.domain.lineup import GameSide


@final
class OpenTheGame:
    def __init__(self, open_game: OpenPlannedGame) -> None:
        self._open = open_game

    async def open(
        self,
        *,
        booking_id: UUID,
        sport: Sport,
        counted: bool,
        first_side: tuple[UUID, ...],
        second_side: tuple[UUID, ...],
        starts_at: Instant,
        at: Instant,
    ) -> UUID:
        game_id = await self._open.execute(
            OpenPlannedGameCommand(
                challenge_id=booking_id,
                sport=sport,
                counted=counted,
                window=None,
                line_up=[
                    *((GameSide.A.value, player) for player in first_side),
                    *((GameSide.B.value, player) for player in second_side),
                ],
                starts_at=starts_at,
            ),
            occurred_at=at,
        )
        # One booking is one game: the fill runs once per booking, so a game
        # already standing for it is a bug upstream, never a retry here.
        invariant(game_id is not None, f"a second game for booking {booking_id}")
        assert game_id is not None
        return game_id
