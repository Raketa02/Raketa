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

from typing import Mapping, final
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
from app.modules.games.domain.ports import GameRepository, PlayerHandles


class _ActOnAResult:
    """What both acts share: load the game, or refuse to admit it exists."""

    def __init__(
        self,
        *,
        games: GameRepository,
        handles: PlayerHandles,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._games = games
        self._handles = handles
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

    async def _named(self, game: Game) -> Mapping[UUID, str]:
        """What the people on this court are called. **Read before the write.**

        The tempting order is the other one — a game's court is frozen at the
        plan, so nothing either act writes could change who is on it, and asking
        after the commit would hold the transaction open for a question about
        somebody else's context. It is wrong for one reason that outweighs that:
        **after the commit, the score has already landed.** A ``users`` that
        cannot answer would then turn a successful entry into a 500, and the
        retry a player makes is refused with ``your_side_has_already_answered``
        about their own score. Before the write, the same outage is an act that
        did not happen — which is what ``docs/adr/0141`` promises.

        **Sorted, because a ``frozenset`` is never the source of a traversal**
        (``docs/adr/0105`` §1). The answer is a mapping and could not observe the
        order, and the rule is stated on the collection rather than on the
        observability for exactly that reason: what is safe today is what changes
        silently.
        """

        return await self._handles.handles_of(sorted(game.line_up.players))

    async def _saved(
        self, game: Game, at: Instant, handles: Mapping[UUID, str]
    ) -> StandingGame:
        """Write the act, then fold the game against the instant it happened at.

        **After the write and against the same instant**, so an entry and the
        ``AWAITING_ANSWER`` it produced are one reading rather than two.
        """

        await self._games.save(game)
        await self._uow.commit()
        return StandingGame.folded(game, now=at, handles=handles)


@final
class StateResult(_ActOnAResult):
    """*This is the score.* The record decides whether that is an entry, a
    correction or a disagreement."""

    async def execute(self, command: StateResultCommand) -> StandingGame:
        at = instant(self._clock.now())
        game = await self._yours(
            game_id=command.game_id, player_id=command.player_id
        )
        handles = await self._named(game)
        game.state_result(by=command.player_id, score=command.score, occurred_at=at)
        return await self._saved(game, at, handles)


@final
class AcceptResult(_ActOnAResult):
    """*That is what happened.* From across the net, and one opponent suffices."""

    async def execute(self, command: AcceptResultCommand) -> StandingGame:
        at = instant(self._clock.now())
        game = await self._yours(
            game_id=command.game_id, player_id=command.player_id
        )
        handles = await self._named(game)
        game.accept_result(by=command.player_id, occurred_at=at)
        return await self._saved(game, at, handles)
