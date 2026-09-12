"""``PlannedGameHandover``, answered by the ``games`` context.

The mirror of ``matchmaking``'s ``ChallengesMutualChallenge``, and it exists for
the same reason: the arrow runs ``challenges -> games``, so this context *could*
call the other's use case directly. It does not, because **what opens a game** is
a choice about wiring and belongs in the composition root with every other choice
of implementation — and because an accept path reaching into somebody else's
aggregate factory would put a second author on *what a game born of a completed
line-up is*.

**It translates one sentence into another and nothing else.** The side codes are
identical strings on both sides on purpose, so the mapping here is a pass-through
rather than a table; a table would be a place for the two spellings to drift.
"""

from __future__ import annotations

from typing import Sequence, final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.games.application.commands import (
    OpenPlannedGameCommand,
    VacateSeatCommand,
)
from app.modules.games.application.open_planned_game import OpenPlannedGame
from app.modules.games.application.vacate_seat import VacateSeat


@final
class GamesPlannedGame:
    """*Everybody accepted* → the ``games`` command that records the arrangement;
    *somebody left* → the one that opens their seat."""

    def __init__(self, games: OpenPlannedGame, departures: VacateSeat) -> None:
        self._games = games
        self._departures = departures

    async def open_planned_game(
        self,
        *,
        challenge_id: UUID,
        sport: Sport,
        counted: bool,
        window: str | None,
        line_up: Sequence[tuple[str, UUID]],
        occurred_at: Instant,
    ) -> UUID | None:
        return await self._games.execute(
            OpenPlannedGameCommand(
                challenge_id=challenge_id,
                sport=sport,
                counted=counted,
                window=window,
                line_up=tuple(line_up),
            ),
            occurred_at=occurred_at,
        )

    async def vacate_seat(
        self, *, challenge_id: UUID, player_id: UUID, occurred_at: Instant
    ) -> None:
        await self._departures.execute(
            VacateSeatCommand(challenge_id=challenge_id, player_id=player_id),
            occurred_at=occurred_at,
        )
