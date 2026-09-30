"""A game opened by a line-up that completed — **or re-seated by the next one.**

It signs the port ``challenges`` declares, and it runs in the transaction of the
accept that filled the last seat: the acceptance and the game it produced commit
together or neither does (``docs/adr/0137``).

**One arrangement is one game.** The accept path is at-least-once under a retry
and this is the only writer, so the check that makes it idempotent lives here —
a second game for one challenge would be two records of one evening, and the day
they disagreed there would be nothing to say which was real. Since
``docs/adr/0162`` the same read answers a second question: a completed line-up
arriving for a game that stands **with a seat open** re-seats that game, and
one arriving for a game standing whole is the retry it always was.

**It does not commit**, for the reason ``OpenChallengeFromMutualInterest`` does
not: the transaction boundary is a decision about the *command*, and the caller
owns it.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.games.application.commands import OpenPlannedGameCommand
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, LineUp, Seating, GameSide
from app.modules.games.domain.ports import GameRepository
from app.modules.player_profile.domain.weekly_hours import Window
from app.shared.ids import new_uuid


@final
class OpenPlannedGame:
    """*Everybody accepted* → a game that has not happened yet."""

    def __init__(self, *, games: GameRepository) -> None:
        self._games = games

    async def execute(
        self, command: OpenPlannedGameCommand, *, occurred_at: Instant
    ) -> UUID | None:
        """The game now standing for this challenge — opened, or re-seated — or
        ``None`` for one that already stands whole.

        The clock is the caller's, and deliberately: the moment this game was
        arranged is the moment the last acceptance was recorded, and reading a
        second clock here would date the game a few milliseconds after the fact
        that caused it. **A re-seat does not re-date it**: ``planned_at`` keeps
        meaning *when it became a game*, and the room's end and the entry window
        are both measured from it.
        """

        line_up = LineUp.of(
            Seating(side=GameSide(side), player_id=player_id)
            for side, player_id in command.line_up
        )
        existing = await self._games.for_challenge(command.challenge_id)
        if existing is not None:
            if existing.line_up.is_complete:
                return None
            existing.reseat(line_up, occurred_at=occurred_at)
            await self._games.save(existing)
            return existing.id

        # The window crosses the port as its code — ``challenges`` hands over an
        # arrangement in primitives and neither context learns the other's
        # types — and becomes a ``Window`` here, at the one place this module
        # meets the wire. A code kept as a string past this line would be a
        # second spelling of a closed enum.
        game = Game.planned(
            game_id=new_uuid(),
            challenge_id=command.challenge_id,
            sport=command.sport,
            kind=GameKind.COUNTED if command.counted else GameKind.FRIENDLY,
            window=None if command.window is None else Window(command.window),
            line_up=line_up,
            occurred_at=occurred_at,
        )
        await self._games.save(game)
        return game.id
