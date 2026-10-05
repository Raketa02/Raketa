"""An open seat taken by a booking's rescue (#545; the mechanics §10.1).
**Inline, told.**

The fourth thing ``bookings`` asks this context to do, after opening the game,
vacating a seat and calling it off (#541, #544), and it runs in the transaction
of the rescue: the seat on the booking and the seat on the game commit together
or neither does — and the room, whose members are the game's line-up, takes the
newcomer in by the same act.

**The moment guard is not here.** ``bookings`` asked whether the seat was there
to take before it recorded the rescue. What the aggregate refuses on its own is
its own half — a game whose hour has come — and a side with no seat open.

**It does not commit**: the transaction boundary is the caller's.
"""

from __future__ import annotations

from typing import final

from app.kernel import Instant, invariant
from app.modules.games.application.commands import TakeASeatCommand
from app.modules.games.domain.lineup import GameSide
from app.modules.games.domain.ports import GameRepository


@final
class TakeASeat:
    """*Somebody took the open seat* → they are on the court."""

    def __init__(self, *, games: GameRepository) -> None:
        self._games = games

    async def execute(self, command: TakeASeatCommand, *, occurred_at: Instant) -> None:
        game = invariant(
            await self._games.for_challenge(command.challenge_id),
            f"a rescue on an arrangement that opened no game: {command.challenge_id}",
        )
        game.take_seat(
            command.player_id, side=GameSide(command.side), occurred_at=occurred_at
        )
        await self._games.save(game)


__all__ = ["TakeASeat"]
