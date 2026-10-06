"""``PlayedCourt``, answered by the ``games`` context.

**The record membership is read from.** A room is opened only by a booked game
(#575), and the game's line-up moves only as somebody leaves it or a rescue
takes the seat (``docs/adr/0162``) — read live, so a departure drops its actor
and a re-seat admits the newcomer.

**It reads through ``GameRepository`` and ``GameDirectory``**, on the argument
the other adapters over ``games`` already make for the same arrow: the
aggregate is where the line-up is, and a second query port declaring the same
read would be a second place for *who is on this court* to be true.

**What crosses is the players and not the sides.** A room draws faces; which side
somebody is on is a fact about a game, and a caller given it would eventually act
on it.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.modules.games.domain.ports import GameDirectory, GameRepository


@final
class GamesPlayedCourt:
    """*Who is on the court of this game?*"""

    def __init__(self, games: GameRepository, directory: GameDirectory) -> None:
        self._games = games
        self._directory = directory

    async def bookings_played_by(self, player_id: UUID) -> frozenset[UUID]:
        """Read through ``playing``, the game list's own read: each booked game
        keeps the booking it was opened from as the arrangement it names."""

        return frozenset(
            game.challenge_id for game in await self._directory.playing(player_id)
        )

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
