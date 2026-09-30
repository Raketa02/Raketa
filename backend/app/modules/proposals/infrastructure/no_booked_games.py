"""``BookedGames`` while nothing can be booked: nobody has a game (#541).

The same stand-in ``NoCourtBookings`` is for a club's courts: a demand whose
provider does not exist yet, answered with the truth — nought — so *games per
week* and *one game per hour* are wired to the port they will read, and the day
a booking can hold a game its adapter is built in the composition root instead.
API tests stand in for it by overriding ``get_booked_games``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import final
from uuid import UUID

from app.kernel import Instant


@final
class NoBookedGamesYet:
    async def starts_of(
        self, player_id: UUID, *, start: Instant, end: Instant
    ) -> Sequence[Instant]:
        return ()
