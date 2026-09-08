"""What this context asks for and nobody is there to answer, answering honestly.

**Nothing here stands in for an absent provider.** Each class below is a null
object **named for the fact it asserts** — ``NoHoldsExist``, not
``NullAccountHoldQuery`` — because *null* reads as *not wired yet*, and both of
these are wired (``docs/adr/0095``, ``docs/adr/0147`` §3).

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

from app.modules.conversations.domain.live import Nudge


@final
class NoHoldsExist:
    """Nobody is under a hold, because nothing on this platform can impose one."""

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        return frozenset()


@final
class NobodyIsFollowing:
    """A ``NudgePublisher`` for a run with **no phone attached to it.**

    A seed run and a command-line outbox drain both append to rooms, and both do
    it on a laptop with nobody's conversation screen open. They get this rather
    than the Redis publisher, and they get it **explicitly** — the parameter is
    required at every call site, so *this delivery is not live* is a sentence
    somebody wrote rather than a default somebody inherited.

    It is not a fail-soft publisher with the store missing: that one degrades
    from a failure and says so in a log line, and this one is the correct answer.
    """

    async def nudge(self, nudge: Nudge) -> None:
        return None
