"""``GameOfCourtQuery``, answered by the ``games`` context.

The fourth adapter on the one arrow ``challenges -> games``, beside the
hand-over, the settled read and the seatable read, and it reads through
``GameRepository`` on ``games_settled_game.py``'s argument: ``for_challenge``
was built to make the opening idempotent inside the accept's own transaction —
*has this challenge already opened a game* — and *which game did it open* is
the same lookup with the id read off the end. A second read declaring the same
join would be a second place for *one arrangement is one game* to be true.

**It translates a game into its id and nothing else.** What crosses this seam
is which of the ids the caller asked about stand for which game; the game's
standing, its court and its ending do not cross, because a challenge read given
them would eventually act on them — and the challenge's own copy of the ending
is the one the row reads (``docs/adr/0172`` §1).
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.modules.games.domain.ports import GameRepository


@final
class GamesGameOfCourt:
    """*Which of these courts have a game, and which game?*"""

    def __init__(self, games: GameRepository) -> None:
        self._games = games

    async def games_of(self, challenge_ids: Collection[UUID]) -> Mapping[UUID, UUID]:
        """The game behind each of these challenges — **and a raise is left to
        travel.**

        **The port is bulk; this implementation of it is a walk**, on
        ``games_settled_game.py``'s argument exactly: ``games`` offers one join
        and it is per challenge, so the loop is here rather than in the caller
        and the day it becomes a single statement nothing above this line
        moves. What it walks is the been-a-game subset of one reader's inbox —
        a list with none for most readers — and ``docs/adr/0172``'s
        consequences name this read as the one to make a single call the day a
        measurement shows it. Sorted, so that the reads happen in the same
        order on every process and under every ``PYTHONHASHSEED``
        (``docs/adr/0105``).
        """

        games: dict[UUID, UUID] = {}
        for challenge_id in sorted(set(challenge_ids)):
            game = await self._games.for_challenge(challenge_id)
            if game is not None:
                games[challenge_id] = game.game_id
        return games


__all__ = ["GamesGameOfCourt"]
