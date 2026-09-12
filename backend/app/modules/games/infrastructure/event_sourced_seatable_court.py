"""``SeatableCourt`` over the repository and the Plan's moment — *may a seat on
this court still change?*

**The guard is written once, here** (``docs/adr/0162`` §4). Two facts decide it
and they live in two contexts: whether the game is still awaiting its entry is
this record's, folded against the caller's instant like every standing here; and
the agreed moment is the Plan's, read through ``AgreedMoment`` and stored
nowhere. The departure, the fill and the acceptance all read this one answer, so
the leaving and the filling cannot come to two verdicts about one instant.

**Keyed by the challenge id**, through ``for_challenge`` — the join the opening's
idempotence already needed, asked one act later.

**Nothing is projected and nothing is stored.** A game whose moment has passed
reads as closed to seating whether or not anything noticed, and a plan moved
forward by a chip reopens it, because the moment is read at the guard.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.games.domain.ports import (
    AgreedMoment,
    GameRepository,
    SeatChange,
)
from app.modules.games.domain.standing import GameStanding


@final
class EventSourcedSeatableCourt:
    """``SeatableCourt`` over ``GameRepository`` and ``AgreedMoment``."""

    def __init__(self, *, games: GameRepository, moments: AgreedMoment) -> None:
        self._games = games
        self._moments = moments

    async def seat_change_on(
        self, challenge_id: UUID, *, now: Instant
    ) -> SeatChange | None:
        """The standing first, then the moment — a ghost is told it is history
        rather than that its Sunday has gone."""

        game = await self._games.for_challenge(challenge_id)
        if game is None:
            return None
        if game.standing_at(now) is not GameStanding.AWAITING_ENTRY:
            return SeatChange.GAME_IS_HISTORY
        agreed = await self._moments.agreed_point_of(game.id)
        if agreed is not None and now >= agreed:
            return SeatChange.MOMENT_PASSED
        return SeatChange.ADMITTED


__all__ = ["EventSourcedSeatableCourt"]
