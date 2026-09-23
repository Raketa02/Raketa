"""A seat vacated because its occupant left the challenge. **Inline, told.**

The second thing ``challenges`` asks this context to do (``docs/adr/0162``), and
it runs in the transaction of the departure: the ``LEFT`` on the seat and the
open seat on the game commit together or neither does, for the reason the
opening does — a player who taps *leave* is told by a screen that cannot yet show
it otherwise.

**The moment guard is not here.** ``challenges`` asked ``SeatableCourt`` before
it recorded the departure, and that port is where the game's standing and the
plan's moment are read together, once. What the aggregate refuses on its own is
its own half — a game that is not awaiting its entry — and somebody who is not
on the court.

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
        """Open one seat on the game this challenge became.

        A challenge that is ``ON`` has a game — the opening runs in the
        acceptance's own transaction — so a departure arriving for a challenge
        with none is a broken precondition rather than a state, and it raises
        rather than being quietly ignored: the ``LEFT`` on the seat would
        otherwise commit with no open seat behind it.
        """

        game = invariant(
            await self._games.for_challenge(command.challenge_id),
            f"a departure from a challenge that opened no game: {command.challenge_id}",
        )
        game.vacate(command.player_id, occurred_at=occurred_at)
        await self._games.save(game)


__all__ = ["VacateSeat"]
