"""A booked game called off. **Inline, told.**

Two acts reach this, both told by ``bookings`` in the transaction of the act
that ends the booking, so the end on the booking and the end on the game commit
together or neither does:

- **the cut-off with a seat open** (#544) — ``CallOffGame``, which names nobody;
- **the club taking the court back** (#547) — ``CallOffTheWholeGame``, whole or
  with a seat open.

**A game that started short is stepped over, and it is the one leniency here**
(#544). A booking's cut-off call-off can arrive after the hour, by which time
a game with a seat open has *started short* — an end the record and the clock
already reached. The act is about the booking, and the game keeps the end it
reached rather than this raising. Every other end is unreachable from a
booking the act admits, so the aggregate's own refusal is left to fire and roll
the act back, which is what a broken precondition should do.

**It does not commit**, for the reason ``VacateSeat`` does not: the transaction
boundary is a decision about the *command*, and the caller owns it.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.games.application.commands import CallOffGameCommand
from app.modules.games.domain.ports import GameRepository
from app.modules.games.domain.standing import GameStanding


@final
class CallOffGame:
    """*The booking was called off at its cut-off* → its game is called off."""

    def __init__(self, *, games: GameRepository) -> None:
        self._games = games

    async def execute(
        self, command: CallOffGameCommand, *, occurred_at: Instant
    ) -> None:
        """End the game this booking opened, if it is still one to end.

        A filled booking has a game — the opening runs in the fill's own
        transaction — so a call-off arriving for a booking with no game behind
        it is a broken precondition rather than a state, and it raises rather
        than being quietly ignored.
        """

        game = invariant(
            await self._games.for_challenge(command.challenge_id),
            f"a call-off of a booking with no game behind it: "
            f"{command.challenge_id}",
        )
        if game.standing_at(occurred_at) is GameStanding.STARTED_SHORT:
            # Already ended by its clock: a booked game short at its cut-off
            # whose call-off arrives after its hour started short (#544), and
            # keeps that.
            return
        game.call_off(by=command.called_by, occurred_at=occurred_at)
        await self._games.save(game)


@final
class CallOffTheWholeGame:
    """*The club took the court back* → the booked game on it is called off,
    whole or with a seat open (#547). Told by ``bookings`` in the club's own
    transaction."""

    def __init__(self, *, games: GameRepository) -> None:
        self._games = games

    async def execute(self, challenge_id: UUID, *, occurred_at: Instant) -> None:
        game = invariant(
            await self._games.for_challenge(challenge_id),
            f"a booking called off with no game behind it: {challenge_id}",
        )
        game.call_off_whole(occurred_at=occurred_at)
        await self._games.save(game)


__all__ = ["CallOffGame", "CallOffTheWholeGame"]
