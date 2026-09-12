"""``SeatableGameQuery``, answered by the ``games`` context.

The third adapter on the one arrow ``challenges -> games``, beside the hand-over
and the settled read, and the first of the three to read a port ``games``
**publishes** rather than its repository: the guard it translates is two facts
from two contexts read together (``docs/adr/0162`` §4), and folding them here
would make this context a second author of a game's standing.

**A word-for-word translation and nothing more.** The two enums are spelled the
same on purpose, so this is identity rather than a table.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.challenges.domain.seatable_game import LineUpChange
from app.modules.games.domain.ports import SeatableCourt


@final
class GamesSeatableGame:
    """*May a seat on this court still change?* — read off ``games``."""

    def __init__(self, courts: SeatableCourt) -> None:
        self._courts = courts

    async def line_up_change_on(
        self, challenge_id: UUID, *, now: Instant
    ) -> LineUpChange | None:
        found = await self._courts.seat_change_on(challenge_id, now=now)
        return None if found is None else LineUpChange(found.value)


__all__ = ["GamesSeatableGame"]
