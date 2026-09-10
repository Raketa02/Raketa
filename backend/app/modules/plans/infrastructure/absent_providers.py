"""What this context asks for and nobody is there to answer, answering honestly.

**Nothing here stands in for an absent provider.** The class below is a null
object **named for the fact it asserts** — ``NoHoldsExist``, not
``NullAccountHoldQuery`` — because *null* reads as *not wired yet*, and this is
wired (``docs/adr/0095``).

**It is the fourth spelling of one empty answer, and the duplication is the
decision.** The matcher, ``challenges`` and ``conversations`` each declare a port
of the same shape against the same absent provider, and this context may not
import any of them: a plan reading a safety fact through somebody else's port
would be exactly the coupling the split exists to avoid. On the day ``cases``
ships, four lines in the composition root change to the same adapter.

**The empty answer is measured rather than stubbed.** Nobody can be held because
nothing on this platform can hold anybody — there is no case, no route and no
record — which is why this is a fact rather than a placeholder, and why the held
arm of the four plan writes is currently unreachable by ``make seed``. That is
stated where the next person will find it rather than left to be discovered.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID


@final
class NoHoldsExist:
    """Nobody is under a hold, because nothing on this platform can impose one."""

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        return frozenset()
