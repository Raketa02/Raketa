"""Reading a player's games back. **The clock is read once, here.**

Every fact a game screen shows is folded from the record against an instant —
the standing, whose turn it is, when each clock runs out — so the instant is read
once for the whole answer and handed down. Two reads of the clock inside one
response is how a list ends up showing a game as awaiting an answer and its own
deadline as passed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.ports import GameDirectory
from app.modules.games.domain.standing import GameStanding


@final
@dataclass(frozen=True, slots=True)
class StandingGame:
    """One game, what it is right now, and the instant that *right now* was.

    **The moment travels with the row** because every remaining fact the
    presentation layer asks for is folded against it — the agreed score, this
    reader's outcome, the two deadlines — and a renderer that read a second clock
    could print a countdown disagreeing with the standing beside it.

    One type, used by the read and by both acts, on ``StandingChallenge``'s
    precedent: a game and its standing are one answer whether the caller just
    changed something or only asked.
    """

    game: Game
    standing: GameStanding
    read_at: Instant

    @classmethod
    def folded(cls, game: Game, *, now: Instant) -> "StandingGame":
        return cls(game=game, standing=game.standing_at(now), read_at=now)


@final
class ReadGames:
    """Every game this player was on the court for, newest arrangement first."""

    def __init__(self, *, games: GameDirectory, clock: Clock) -> None:
        self._games = games
        self._clock = clock

    async def execute(
        self, player_id: UUID
    ) -> tuple[Instant, tuple[StandingGame, ...]]:
        """The instant everything was read at, and the games as they stood in it.

        The instant travels back with the answer because the presentation layer
        has deadlines to render against it, and rendering a countdown against a
        second clock read would let a game's remaining time disagree with the
        standing beside it.
        """

        now = instant(self._clock.now())
        found = await self._games.playing(player_id)
        return now, tuple(
            sorted(
                (StandingGame.folded(game, now=now) for game in found),
                key=lambda one: one.game.planned_at,
                reverse=True,
            )
        )
