"""The one provider this context needs and does not have, answering honestly.

**Nothing here stands in for an absent provider.** The class below is a null
object **named for the fact it asserts** — ``NoHoldsExist``, not
``NullAccountHoldQuery`` — because *null* reads as *not wired yet*, and this is
wired (``docs/adr/0095``). It is not a stub returning a plausible answer: it says
something true about this platform today, and it stops being true on the day
``cases`` lands, at which point it is swapped for a real adapter and every caller
carries straight over.

**A gate may be honestly empty; a term may never be honestly neutral.** Nobody can
be held because nothing can hold anybody — a real, measured absence — so the hold
gate ships true-over-empty and its zero is real.

**It is the matcher's null object, spelled a second time, and the duplication is
the decision.** The matcher declares a port of the same shape against the same
absent provider, and this context may not import it: the arrow runs
``matchmaking -> challenges`` and never back, so sharing would mean a send reading
a safety fact through the matcher. A duplicated *empty answer about a context that
does not exist* is not what that fence was guarding — and on the day ``cases``
ships, both lines in the composition root change to the same adapter.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID


@final
class NoHoldsExist:
    """Nobody is under a hold, because nothing on this platform can impose one.

    The ``cases`` context does not exist: there is no route, no aggregate and no
    table through which a hold could be taken. So this is a measured emptiness
    rather than a gate switched off, and the send that consults it is genuinely
    fail-closed — it is asking a question whose true answer today is *nobody*.
    """

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        return frozenset()
