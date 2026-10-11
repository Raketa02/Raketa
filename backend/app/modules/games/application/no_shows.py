"""Somebody did not come to a booked game, and their answer (#547; the
mechanics §15.3, §15.4).

**Two acts, the result's own shape**: the players who came report one who did
not, where they would enter the result, and the reported player disputes it
inside their day. Neither confirms anything: a report stands when its day
passes in silence, which is a clock, and is proved by moving one.

Nothing at a club's desk is asked: desk check-in is removed (#651).
"""

from __future__ import annotations

from typing import final

from app.kernel import instant
from app.modules.games.application.answer_result import ActOnAGame
from app.modules.games.application.commands import (
    DisputeANoShowCommand,
    ReportANoShowCommand,
)
from app.modules.games.application.read_games import StandingGame


@final
class ReportANoShow(ActOnAGame):
    """*Kuba didn't come* — by a player who came."""

    async def execute(self, command: ReportANoShowCommand) -> StandingGame:
        at = instant(self._clock.now())
        game = await self._yours(game_id=command.game_id, player_id=command.player_id)
        names = await self._named(game)
        game.report_no_show(
            by=command.player_id, absent=command.absent_id, occurred_at=at
        )
        return await self._saved(game, at, names)


@final
class DisputeANoShow(ActOnAGame):
    """*I was there* — by the player reported, inside their day."""

    async def execute(self, command: DisputeANoShowCommand) -> StandingGame:
        at = instant(self._clock.now())
        game = await self._yours(game_id=command.game_id, player_id=command.player_id)
        names = await self._named(game)
        game.dispute_no_show(by=command.player_id, occurred_at=at)
        return await self._saved(game, at, names)


__all__ = ["DisputeANoShow", "ReportANoShow"]
