"""``GameResults``, answered by the ``games`` context (#542).

**A booked game is an ordinary Game**, opened by its booking (``docs/adr/0189``
§5), so where its result stands is read off that aggregate, folded with its own
``standing_at`` — never a second fold of the result here — and translated into
this context's words at the seam.

**Whose agreement a score waits on is the Game's own rule**
(``Game.awaits_agreement_from``), asked of it and never restated here — and so
is whose dispute a report of not turning up waits on (#547): the reported
player's, while its day runs.

**Which games a score may still wait on** is asked of the Games context's own
read (``ScoredGames``, #613) with its own clock: a score waits a day from when
it was last put on the table (``scores_still_waiting_since``) — ids over the
stream index, nothing folded.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.kernel import Instant, exhaustive
from app.modules.games.domain.ports import GameRepository, ScoredGames
from app.modules.games.domain.standing import GameStanding
from app.modules.games.domain.windows import scores_still_waiting_since
from app.modules.proposals.domain.home import GameResult, ResultStage


@final
class GamesGameResults:
    def __init__(self, games: GameRepository, scored: ScoredGames) -> None:
        self._games = games
        self._scored = scored

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
                you_may_dispute=game.may_dispute(reader, now=now),
            )
        return results

    async def waiting_among(
        self, game_ids: Collection[UUID], *, now: Instant
    ) -> Collection[UUID]:
        return await self._scored.scored_since(
            game_ids, since=scores_still_waiting_since(now)
        )


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
        case GameStanding.DISPUTED:
            return ResultStage.DISPUTED
        case GameStanding.NEVER_PLAYED:
            return ResultStage.NEVER_PLAYED
        case GameStanding.CALLED_OFF:
            return ResultStage.CALLED_OFF
        case GameStanding.STARTED_SHORT:
            return ResultStage.STARTED_SHORT
        case GameStanding.NO_SHOW_REPORTED:
            return ResultStage.NO_SHOW_REPORTED
        case GameStanding.NO_SHOW:
            return ResultStage.NO_SHOW
        case _:
            exhaustive(standing)
