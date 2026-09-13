"""*I am out.* The one act that takes a yes back, and the game is told where
there is one.

**A yes can be taken back before the court is whole, and a court is over when
one is left** (``docs/adr/0165``). The act lands on the challenge — the seat
that reopens is the challenge's, and the fill, the pool, the pair rule and the
room's line are all keyed on it — and where the court has become a game
(``docs/adr/0162``), that game is told in the same transaction, the shape the
opening already takes: the ``LEFT`` on the seat and the open seat on the game
commit together or neither does. A court that was never a game hands over
nothing: what the departure did to it, the fold already says.

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
   each refuse (``seat_change.py``). A half-built court costs no read and has no
   moment to guard — a plan may name one (``docs/adr/0164``), and it guards
   nothing until there is a game whose result a no-show could block. The
   standing is asked before the game, so an ended court that has been a game is
   refused as one.
4. **The record**: the aggregate refuses an ended court and a seat that is not an
   accepted one of the caller's, and writes ``SeatLeft``.
5. **The hand-over, where there is a game** — the seat opens on it — **and the
   ending rule, asked here rather than folded** (``docs/adr/0165`` §3). Before a
   game the fold reaches the ending itself: one player left with nobody
   deciding is ``DECLINED``, and the room ends with its challenge. On a game the
   fold does not end the court (``docs/adr/0162`` §2), so this asks
   ``is_deserted_at`` after recording the departure and, when it fires, hands
   ``call_off`` over on the same port — the seat vacated first, then the end,
   so the record reads in the order it happened — with ``called_by`` the
   leaver, whose departure is what ended it. The game is ``CALLED_OFF``, and the
   room is destroyed as for any call-off, told by the game's own end. Singles
   included: an opponent who leaves calls the game off, and doubles fill down to
   two before the last one alone ends it.
6. **The commit and the redraw.**
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
    """One person leaves a court they had agreed to. **Their seat reopens** — and
    where they were the last but one on a game, the game is called off."""

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
        if challenge.has_become_a_game():
            # **The game is told in this transaction**, so the ``LEFT`` on the
            # seat and the open seat on the game commit together or neither
            # does. A court that never became a game hands over nothing.
            await self._planned_games.vacate_seat(
                challenge_id=challenge.id, player_id=command.player_id, occurred_at=at
            )
            if challenge.is_deserted_at(at):
                # **The departure that leaves one player on the court ends
                # it** (``docs/adr/0165`` §3), and only the challenge can say
                # so — the game's line-up cannot tell an open seat from one
                # that is asked. The seat first, then the end, so the record
                # reads in the order it happened.
                await self._planned_games.call_off(
                    challenge_id=challenge.id, by=command.player_id, occurred_at=at
                )
        return await self._committed(challenge, standing, at)


__all__ = ["LeaveGame"]
