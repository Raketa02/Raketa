"""A game called off because its court was ended. **Inline, told.**

The third thing ``challenges`` asks this context to do (``docs/adr/0163``), and
it runs in the transaction of the act that ends the court: the ``WITHDRAWN`` on
the challenge and the end on the game commit together or neither does, for the
reason the opening and the departure do — the player who taps is told by a
screen that cannot yet show it otherwise. **And in the transaction of a
departure** (``docs/adr/0165`` §3): the one that leaves one player on the court
with nobody deciding ends it, and the challenge — the only record that can tell
an open seat from one that is asked — hands the call-off over right after the
seat.

**Whose act it is was decided one context over.** The challenge admitted the
withdraw — any player's on the court (``docs/adr/0165`` §5) — or recorded the
departure, and what the aggregate refuses on its own is its own invariant: a
game awaiting its entry with a seat open, and somebody who was on the court.

**A ghost is stepped over, and so is a game already called off — and those are
the two leniencies here** (``docs/adr/0163`` §6, ``docs/adr/0165`` §3). A
reopened court can outlive its game's entry window — nobody filled the seat,
the window closed, the game is ``NEVER_PLAYED`` and the challenge still stands
``LINE_UP_INCOMPLETE``, holding its pair. The withdraw is that court's only
exit, so it is admitted, and the ghost stays the end it already is rather than
this raising and holding two people apart for the life of the database. And a
departure that leaves one player on a game calls it off with the challenge
still standing, so a withdraw can reach a game that is ``CALLED_OFF`` already:
the same case, and the end it reached — dated and named by the departure —
stays. What is never done is un-ending, or re-ending, either: a call-off that
reached a ghost would flip a card the platform has already drawn, and a second
``GameCalledOff`` would be two records of one end. **Exactly two standings are
stepped over.** Every other end is unreachable from a challenge the withdraw
admits — a played game has a whole court, and a whole court is a challenge that
is ``ON`` — so the aggregate's own refusal is left to fire and roll the
withdrawal back, which is what a broken precondition should do.

**It does not commit**, for the reason ``VacateSeat`` does not: the transaction
boundary is a decision about the *command*, and the caller owns it.
"""

from __future__ import annotations

from typing import final

from app.kernel import Instant, invariant
from app.modules.games.application.commands import CallOffGameCommand
from app.modules.games.domain.ports import GameRepository
from app.modules.games.domain.standing import GameStanding


#: The two ends a reopened court's game can have reached before the court is
#: withdrawn, and which the withdraw steps over rather than re-ending.
_ALREADY_OVER = frozenset({GameStanding.NEVER_PLAYED, GameStanding.CALLED_OFF})


@final
class CallOffGame:
    """*The challenge was withdrawn* → the game it became is called off."""

    def __init__(self, *, games: GameRepository) -> None:
        self._games = games

    async def execute(
        self, command: CallOffGameCommand, *, occurred_at: Instant
    ) -> None:
        """End the game this challenge became, if it is still one to end.

        A challenge that has been ``ON`` has a game — the opening runs in the
        acceptance's own transaction — so a withdrawal arriving for a court
        that has been a game with no game behind it is a broken precondition
        rather than a state, and it raises rather than being quietly ignored:
        the ``WITHDRAWN`` on the challenge would otherwise commit with a game
        still standing behind it.
        """

        game = invariant(
            await self._games.for_challenge(command.challenge_id),
            f"a withdrawal of a court that has been a game, with no game behind "
            f"it: {command.challenge_id}",
        )
        if game.standing_at(occurred_at) in _ALREADY_OVER:
            # Already ended — by its clock, or by the departure that left one
            # player on it. The withdraw is about the challenge, and the game
            # keeps the end it reached.
            return
        game.call_off(by=command.called_by, occurred_at=occurred_at)
        await self._games.save(game)


__all__ = ["CallOffGame"]
