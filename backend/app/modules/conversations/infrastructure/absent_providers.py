"""The one provider this context needs and does not have, answering honestly.

**Nothing here stands in for an absent provider.** The class below is a null
object **named for the fact it asserts** — ``NoHoldsExist``, not
``NullAccountHoldQuery`` — because *null* reads as *not wired yet*, and this is
wired (``docs/adr/0095``).

**It is the third spelling of one empty answer, and the duplication is the
decision.** The matcher and ``challenges`` each declare a port of the same shape
against the same absent provider, and this context may not import either: a room
reading a safety fact through the matcher would be exactly the coupling
``docs/adr/0146`` split these contexts to avoid. On the day ``cases`` ships,
three lines in the composition root change to the same adapter.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID


@final
class NoHoldsExist:
    """Nobody is under a hold, because nothing on this platform can impose one."""

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        return frozenset()
