"""Reading a player's games back. **The clock is read once, here.**

Every fact a game screen shows is folded from the record against an instant —
the standing, whose turn it is, when each clock runs out — so the instant is read
once for the whole answer and handed down. Two reads of the clock inside one
response is how a list ends up showing a game as awaiting an answer and its own
deadline as passed.

**The names are read once too, and for a whole list.** Sixteen people across
four games is one question, asked about the union of everybody who sat on any of
those courts — not one question per seat, and not one per game
(``docs/adr/0141``) — and, since ``docs/adr/0172`` §4, whoever called a game off,
whose seat is vacated and cannot supply the name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, final
from uuid import UUID

from app.kernel import Clock, Instant, instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.ports import GameDirectory, PlayerNames
from app.modules.games.domain.standing import GameStanding


@final
@dataclass(frozen=True, slots=True)
class StandingGame:
    """One game, what it is right now, the instant that *right now* was, and what
    the people on its court are called.

    **The moment travels with the row** because every remaining fact the
    presentation layer asks for is folded against it — the agreed score, this
    reader's outcome, the two deadlines — and a renderer that read a second clock
    could print a countdown disagreeing with the standing beside it.

    **The names travel with it for the opposite reason**: they are folded
    against nothing. They are the one thing on a game that is not derived from
    the record and the clock, and they ride here rather than being fetched in the
    presentation layer because a route that awaited anything would be a route
    that could await it once per seat.

    ``names`` is keyed by player id and a seat may be missing from it — an
    account ``users`` no longer has. That is a ``None`` on the wire and a side on
    the screen, never a dropped seat.

    One type, used by the read and by both acts, on ``StandingChallenge``'s
    precedent: a game and its standing are one answer whether the caller just
    changed something or only asked.
    """

    game: Game
    standing: GameStanding
    read_at: Instant
    names: Mapping[UUID, str]

    @classmethod
    def folded(
        cls, game: Game, *, now: Instant, names: Mapping[UUID, str]
    ) -> "StandingGame":
        return cls(
            game=game,
            standing=game.standing_at(now),
            read_at=now,
            names=names,
        )


@final
class ReadGames:
    """Every game this player was on the court for, newest arrangement first."""

    def __init__(
        self, *, games: GameDirectory, names: PlayerNames, clock: Clock
    ) -> None:
        self._games = games
        self._names = names
        self._clock = clock

    async def execute(
        self, player_id: UUID
    ) -> tuple[Instant, tuple[StandingGame, ...]]:
        """The instant everything was read at, and the games as they stood in it.

        The instant travels back with the answer because the presentation layer
        has deadlines to render against it, and rendering a countdown against a
        second clock read would let a game's remaining time disagree with the
        standing beside it.

        **One name read for the whole list**, over the union of the courts: a
        player who appears in three of your games is asked about once, however
        many games there are. A list of no games still asks — about nobody, which
        the adapter answers without a round trip.

        **The union is sorted on the way out**, because a set is never the source
        of a traversal (``docs/adr/0105`` §1). Nothing downstream could observe
        the order — the answer is a mapping keyed by id — and the rule is stated
        on the collection rather than on what happens to be observable, because
        that is what changes silently.
        """

        now = instant(self._clock.now())
        found = await self._games.playing(player_id)
        names = await self._names.names_of(
            sorted(
                {player for game in found for player in game.line_up.players}
                | {game.called_off_by for game in found if game.called_off_by}
            )
        )
        return now, tuple(
            sorted(
                (StandingGame.folded(game, now=now, names=names) for game in found),
                key=lambda one: one.game.planned_at,
                reverse=True,
            )
        )
