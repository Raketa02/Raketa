"""A game called off because its court was ended. **Inline, told.**

The third thing ``challenges`` asks this context to do (``docs/adr/0163``), and
it runs in the transaction of the act that ends the court: the ``CALLED_OFF`` on
the challenge and the end on the game commit together or neither does, for the
reason the opening and the departure do — the player who taps is told by a
screen that cannot yet show it otherwise. **And in the transaction of a
departure** (``docs/adr/0165`` §3): the one that leaves one player on the court
with nobody deciding ends it, and the challenge — the only record that can tell
an open seat from one that is asked — records its own ending and hands the
call-off over right after the seat (``docs/adr/0172`` §1).

**Whose act it is was decided one context over.** The challenge admitted the
call-off — any player's on the court (``docs/adr/0165`` §5) — or recorded the
departure, and what the aggregate refuses on its own is its own invariant: a
game awaiting its entry with a seat open, and somebody who was on the court.

**A ghost is stepped over, and it is the one leniency here**
(``docs/adr/0163`` §6, ``docs/adr/0172`` §4). A reopened court can outlive its
game's entry window — nobody filled the seat, the window closed, the game is
``NEVER_PLAYED`` and the challenge still stands ``LINE_UP_INCOMPLETE``, holding
its pair. *Call it off* is that court's only exit, so it is admitted — the
challenge is ``CALLED_OFF`` with the presser on its record — and the ghost stays
the end it already is rather than this raising and holding two people apart for
the life of the database. A call-off that reached a ghost would flip a card the
platform has already drawn. **Exactly one standing is stepped over.** A game
already called off used to be the second, because a departure could call a game
off with the challenge still standing; the departure now records the court's
ending too (``docs/adr/0172`` §1), so the challenge is over before a second
act could reach the game, and every other end is unreachable from a challenge
the act admits — a played game has a whole court, and a whole court is a
challenge that is ``ON``. So the aggregate's own refusal is left to fire and
roll the act back, which is what a broken precondition should do.

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
    """*The court was called off* → the game it became is called off."""

    def __init__(self, *, games: GameRepository) -> None:
        self._games = games

    async def execute(
        self, command: CallOffGameCommand, *, occurred_at: Instant
    ) -> None:
        """End the game this challenge became, if it is still one to end.

        A challenge that has been ``ON`` has a game — the opening runs in the
        acceptance's own transaction — so a call-off arriving for a court that
        has been a game with no game behind it is a broken precondition rather
        than a state, and it raises rather than being quietly ignored: the
        ``CALLED_OFF`` on the challenge would otherwise commit with a game
        still standing behind it.
        """

        game = invariant(
            await self._games.for_challenge(command.challenge_id),
            f"a call-off of a court that has been a game, with no game behind "
            f"it: {command.challenge_id}",
        )
        if game.standing_at(occurred_at) in (
            GameStanding.NEVER_PLAYED,
            GameStanding.STARTED_SHORT,
        ):
            # Already ended by its clock — the one end a reopened court's game
            # can have reached before the court is called off, stepped over
            # rather than re-ended. The act is about the challenge, and the
            # game keeps the end it reached. A booked game short at its cut-off
            # whose call-off arrives after its hour has the second such end
            # (#544): it started short, and keeps that.
            return
        game.call_off(by=command.called_by, occurred_at=occurred_at)
        await self._games.save(game)


@final
class CallOffTheWholeGame:
    """*The club took the court back* → the booked game on it is called off,
    whole or with a seat open (#547). Told by ``bookings`` in the club's own
    transaction, its booking's id where a challenge's is."""

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
