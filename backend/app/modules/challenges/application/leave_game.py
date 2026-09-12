"""*I am out.* The one act on a court that has been a game, and the game is told.

**A game's line-up is frozen until somebody leaves it** (``docs/adr/0162``). The
act lands on the challenge — the seat that reopens is the challenge's, and the
fill, the pool, the pair rule and the room's line are all keyed on it — and the
game this court became is told in the same transaction, the shape the opening
already takes: the ``LEFT`` on the seat and the open seat on the game commit
together or neither does.

**The order below is the design**, and each refusal is asked before anything the
one after it would disclose.

1. **Whose act it is.** The caller holds an **accepted** seat, or the refusal is
   ``challenge_not_found`` — ``challenge_of_yours``' one code for two cases,
   extended to a third. Somebody whose seat is awaiting, declined, lapsed or
   already left is told what a stranger is told, because a departure is the one
   act whose refusal must not confirm that they *were* on this court a moment
   ago.
2. **Their own hold**, with the code a search returns, read through the same
   fail-closed gate every other act here reads it through. A departure writes a
   line into a room other people are in, which is reach (``docs/adr/0148`` §9).
3. **The game's answer**, on a court that has been a game and only there: a game
   that has happened, or never will, and a game whose agreed moment has passed
   each refuse (``seat_change.py``). A court that was never a game costs no read
   and meets the aggregate's own refusal instead — which is what makes this order
   the same as *standing, then moment*: the game is asked only where the standing
   would have admitted the act, and an ended court that has been a game does not
   exist today, since the one ending it could reach is refused while it stands.
4. **The record**: the aggregate refuses a court that is not a game and a seat
   that is not an accepted one of the caller's, and writes ``SeatLeft``.
5. **The hand-over**, then the commit and the redraw.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.challenges.application.challenge_of_yours import AChallengeOfYours
from app.modules.challenges.application.commands import LeaveGameCommand
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.application.read_challenges import StandingChallenge
from app.modules.challenges.application.seat_change import (
    refuse_a_court_closed_to_seating,
)
from app.modules.challenges.domain.errors import NoChallengeOfYoursHasThatId
from app.modules.challenges.domain.planned_game import PlannedGameHandover
from app.modules.challenges.domain.ports import ChallengeRepository, PlayerHandles
from app.modules.challenges.domain.seatable_game import SeatableGameQuery
from app.shared.domain.errors import AccountHeld


@final
class LeaveGame(AChallengeOfYours):
    """One person leaves the game this court became. **Their seat reopens.**"""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        handles: PlayerHandles,
        safety: CourtSafety,
        games: SeatableGameQuery,
        uow: UnitOfWork,
        clock: Clock,
        planned_games: PlannedGameHandover,
    ) -> None:
        super().__init__(challenges=challenges, handles=handles, uow=uow, clock=clock)
        self._safety = safety
        self._games = games
        self._planned_games = planned_games

    async def execute(self, command: LeaveGameCommand) -> StandingChallenge:
        at = instant(self._clock.now())
        challenge = await self._yours(command.challenge_id, command.player_id)
        seat = challenge.seat_of(command.player_id)
        if seat is None or not seat.is_accepted():
            raise NoChallengeOfYoursHasThatId()
        # **Through the gate that fails closed**, exactly as the send and the
        # fill read it: an outage refuses with ``challenge_gates_unavailable``
        # rather than being a 500 on somebody's departure.
        if command.player_id in await self._safety.held_among([command.player_id]):
            raise AccountHeld("this account is under a hold")
        await refuse_a_court_closed_to_seating(challenge, at=at, games=self._games)
        challenge.leave(command.player_id, occurred_at=at)
        standing = await self._written(challenge, at)
        # **The game is told in this transaction**, so the ``LEFT`` on the seat
        # and the open seat on the game commit together or neither does.
        await self._planned_games.vacate_seat(
            challenge_id=challenge.id, player_id=command.player_id, occurred_at=at
        )
        return await self._committed(challenge, standing, at)


__all__ = ["LeaveGame"]
