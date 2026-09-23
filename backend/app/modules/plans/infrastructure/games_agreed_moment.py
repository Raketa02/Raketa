"""``AgreedMoment``, answered by the Plan — the one thing ``games`` asks of it.

**The arrow does not move** (``docs/adr/0145`` §4, ``docs/adr/0162`` §4). ``games``
declares the port in its own words and imports nothing from here; this adapter
signs it structurally — it need not even import the ``Protocol`` — over the
Plan's own read, which is the shape ``SeatableGameQuery`` already has one arrow
over. ``.importlinter`` keeps holding *games does not know the plan*.

**Keyed by the challenge the game was opened from**, because that is the plan's
own id (``docs/adr/0164`` §1) and it is a fact every game carries; ``games``
asks in the currency it already holds and this adapter translates nothing.

**Through the repository rather than the directory**, because the question is
about one court and ``load`` answers an unwritten plan — whose ``agreed_point``
is ``None`` — rather than nothing, which is the honest answer for a court nobody
has agreed a day for.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.plans.domain.ports import PlanRepository


@final
class PlansAgreedMoment:
    """*When has this game been agreed for?* — the Plan's answer."""

    def __init__(self, plans: PlanRepository) -> None:
        self._plans = plans

    async def agreed_point_of(self, challenge_id: UUID) -> Instant | None:
        plan = await self._plans.load(challenge_id)
        return plan.agreed_point


__all__ = ["PlansAgreedMoment"]
