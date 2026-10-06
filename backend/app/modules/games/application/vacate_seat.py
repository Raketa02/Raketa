"""A seat vacated because its occupant left the booking (#544). **Inline, told.**

It runs in the transaction of the departure: the seat on the booking and the
open seat on the game commit together or neither does — a player who taps
*leave* is told by a screen that cannot yet show it otherwise.

**Whether the booking may still be left is not asked here.** ``bookings``
asked before it recorded the departure. What the aggregate refuses on its own
is its own half — a game that is not awaiting its entry — and somebody who is
not on the court.

**It does not commit**, for the reason ``OpenPlannedGame`` does not: the
transaction boundary is a decision about the *command*, and the caller owns it.
"""

from __future__ import annotations

from typing import final

from app.kernel import Instant, invariant
from app.modules.games.application.commands import VacateSeatCommand
from app.modules.games.domain.ports import GameRepository


@final
class VacateSeat:
    """*Somebody left* → their seat on the game is open."""

    def __init__(self, *, games: GameRepository) -> None:
        self._games = games

    async def execute(
        self, command: VacateSeatCommand, *, occurred_at: Instant
    ) -> None:
        """Open one seat on the game this booking opened.

        A booking that was filled has a game — the opening runs in the fill's
        own transaction — so a departure arriving for a booking with none is a
        broken precondition rather than a state, and it raises rather than
        being quietly ignored.
        """

        game = invariant(
            await self._games.for_challenge(command.challenge_id),
            f"a departure from a booking that opened no game: {command.challenge_id}",
        )
        game.vacate(command.player_id, occurred_at=occurred_at)
        await self._games.save(game)


__all__ = ["VacateSeat"]
