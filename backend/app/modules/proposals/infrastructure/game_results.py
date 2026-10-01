"""``GameResults``, answered by the ``games`` context (#542).

**A booked game is an ordinary Game**, opened by its booking (``docs/adr/0189``
§5), so where its result stands is read off that aggregate, folded with its own
``standing_at`` — never a second fold of the result here — and translated into
this context's words at the seam.

**Whose agreement a score waits on is the Game's own rule**
(``Game.awaits_agreement_from``), asked of it and never restated here.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.kernel import Instant, exhaustive
from app.modules.games.domain.ports import GameRepository
from app.modules.games.domain.standing import GameStanding
from app.modules.proposals.domain.home import GameResult, ResultStage


@final
class GamesGameResults:
    def __init__(self, games: GameRepository) -> None:
        self._games = games

    async def of(
        self, game_ids: Collection[UUID], *, reader: UUID, now: Instant
    ) -> Mapping[UUID, GameResult]:
        results: dict[UUID, GameResult] = {}
        for game_id in sorted(set(game_ids)):
            game = await self._games.load(game_id)
            if game is None:
                continue
            results[game_id] = GameResult(
                stage=_stage(game.standing_at(now)),
                awaits_your_agreement=game.awaits_agreement_from(reader, now=now),
            )
        return results


def _stage(standing: GameStanding) -> ResultStage:
    match standing:
        case GameStanding.AWAITING_ENTRY:
            return ResultStage.ENTRY_OPEN
        case GameStanding.AWAITING_ANSWER:
            return ResultStage.SCORE_TO_ANSWER
        case GameStanding.CONFIRMED:
            return ResultStage.CONFIRMED
        case GameStanding.UNSCORED:
            return ResultStage.UNSCORED
        case GameStanding.NEVER_PLAYED:
            return ResultStage.NEVER_PLAYED
        case GameStanding.CALLED_OFF:
            return ResultStage.CALLED_OFF
        case GameStanding.STARTED_SHORT:
            return ResultStage.STARTED_SHORT
        case _:
            exhaustive(standing)
