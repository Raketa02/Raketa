"""``PlayedCourt``, answered by the ``games`` context.

**The other half of *one rule read against two records*.** A game's line-up is
frozen until somebody leaves it (``docs/adr/0162``) and moves only as
``challenges`` tells it, so this is the record membership is read from once a
line-up has completed — read live, so a departure drops its actor and a re-seat
admits the newcomer — and it is asked only about rooms whose ``game_id`` is set,
which means the two records never both answer about one room.

**It reads through ``GameRepository``**, on the argument
``challenges/infrastructure/games_settled_game.py`` already makes for the same
arrow: the aggregate is where the line-up is, and a second query port declaring
the same read would be a second place for *who was on this court* to be true.

**What crosses is the players and not the sides.** A room draws faces; which side
somebody was on is a fact about a game, and a caller given it would eventually act
on it.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.modules.games.domain.ports import GameRepository


@final
class GamesPlayedCourt:
    """*Who was on the court of this game?*"""

    def __init__(self, games: GameRepository) -> None:
        self._games = games

    async def line_ups_of(
        self, game_ids: Collection[UUID]
    ) -> Mapping[UUID, frozenset[UUID]]:
        line_ups: dict[UUID, frozenset[UUID]] = {}
        for game_id in sorted(set(game_ids)):
            game = await self._games.load(game_id)
            if game is None:
                continue
            line_ups[game_id] = game.line_up.players
        return line_ups

    async def game_of(self, challenge_id: UUID) -> UUID | None:
        """Read through ``for_challenge``, which is the join this already is.

        That method was built to make the game's opening idempotent inside the
        accept's own transaction — *has this challenge already opened a game* —
        and this is the same question asked a poll later. A second read declaring
        the same join would be a second place for *one arrangement is one game*
        to be true.
        """

        game = await self._games.for_challenge(challenge_id)
        return None if game is None else game.game_id
