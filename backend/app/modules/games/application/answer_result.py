"""The two acts a player performs on a result, and the one thing they share.

**Stating a score and accepting one are two use cases, not a flag.** They are
different things to explain and different things to measure: one puts a claim in
front of the people who were there, and the other is the whole of the evidence
that a claim was true.

**Neither of them confirms anything.** There is no ``ConfirmResult`` here and
nothing anywhere in this context is called *confirm*: a result is confirmed when
a clock passes, which is somebody not doing something, and no use case can be
written for that. Silence confirming is proved by advancing a clock and reading
the standing back.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.games.application.commands import (
    AcceptResultCommand,
    StateResultCommand,
)
from app.modules.games.application.read_games import StandingGame
from app.modules.games.domain.errors import YouWereNotOnThisCourt
from app.modules.games.domain.game import Game
from app.modules.games.domain.ports import GameRepository


class _ActOnAResult:
    """What both acts share: load the game, or refuse to admit it exists."""

    def __init__(
        self,
        *,
        games: GameRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._games = games
        self._uow = uow
        self._clock = clock

    async def _yours(self, *, game_id: UUID, player_id: UUID) -> Game:
        """That game, if this player was on its court.

        **The two ways this refuses are one code**: no such game, and a game you
        did not play. Separating them would answer *is this game id real* about
        four strangers' evening — and the aggregate raises the same refusal a
        moment later anyway, so the split would buy an information leak and
        nothing else.
        """

        game = await self._games.load(game_id)
        if game is None or player_id not in game.line_up.players:
            raise YouWereNotOnThisCourt()
        return game

    async def _saved(self, game: Game, at: Instant) -> StandingGame:
        """Write the act, then fold the game against the instant it happened at.

        **After the write and against the same instant**, so an entry and the
        ``AWAITING_ANSWER`` it produced are one reading rather than two.
        """

        await self._games.save(game)
        await self._uow.commit()
        return StandingGame.folded(game, now=at)


@final
class StateResult(_ActOnAResult):
    """*This is the score.* The record decides whether that is an entry, a
    correction or a disagreement."""

    async def execute(self, command: StateResultCommand) -> StandingGame:
        at = instant(self._clock.now())
        game = await self._yours(
            game_id=command.game_id, player_id=command.player_id
        )
        game.state_result(by=command.player_id, score=command.score, occurred_at=at)
        return await self._saved(game, at)


@final
class AcceptResult(_ActOnAResult):
    """*That is what happened.* From across the net, and one opponent suffices."""

    async def execute(self, command: AcceptResultCommand) -> StandingGame:
        at = instant(self._clock.now())
        game = await self._yours(
            game_id=command.game_id, player_id=command.player_id
        )
        game.accept_result(by=command.player_id, occurred_at=at)
        return await self._saved(game, at)
