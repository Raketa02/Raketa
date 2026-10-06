"""A game opened by a booking (#541).

It runs in the transaction of the fill that booked the court: the booking and
the game it produced commit together or neither does (``docs/adr/0137``).

**One arrangement is one game.** This is the only writer, so the check that
makes it idempotent lives here — a second game for one booking would be two
records of one evening, and the day they disagreed there would be nothing to
say which was real. A booking that already has a game is answered ``None``.

**It does not commit**: the transaction boundary is a decision about the
*command*, and the caller owns it.
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
    """*The court is booked* → a game that has not happened yet."""

    def __init__(self, *, games: GameRepository) -> None:
        self._games = games

    async def execute(
        self, command: OpenPlannedGameCommand, *, occurred_at: Instant
    ) -> UUID | None:
        """The game now standing for this booking, or ``None`` for one that
        already has a game.

        The clock is the caller's, and deliberately: the moment this game was
        arranged is the moment the booking was recorded, and reading a second
        clock here would date the game a few milliseconds after the fact that
        caused it.
        """

        if await self._games.for_challenge(command.challenge_id) is not None:
            return None

        # The window crosses the port as its code and becomes a ``Window`` here,
        # at the one place this module meets the wire. A code kept as a string
        # past this line would be a second spelling of a closed enum.
        game = Game.planned(
            game_id=new_uuid(),
            challenge_id=command.challenge_id,
            sport=command.sport,
            kind=GameKind.COUNTED if command.counted else GameKind.FRIENDLY,
            window=None if command.window is None else Window(command.window),
            line_up=LineUp.of(
                Seating(side=GameSide(side), player_id=player_id)
                for side, player_id in command.line_up
            ),
            occurred_at=occurred_at,
            starts_at=command.starts_at,
        )
        await self._games.save(game)
        return game.id
