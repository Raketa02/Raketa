"""One row of ``GET /plans``, and the answer every plan write gives back.

**A plan and the anchor its horizon runs from, and nothing else.** The Plan
stores nothing it can derive and nothing it borrows (``docs/adr/0144``,
``docs/adr/0164`` §4): the anchor is the court's — the challenge's send until
the game exists, then the game's ``planned_at`` — read through the port per
request and never written. But a client draws the day chips from it, so it has
to cross the wire beside the slots, and this is the seam where the two are put
side by side: after the port has answered and before the schema is built.

**The write use cases answer it too**, because *the plan as it now stands* is
what a slot write returns and a row without its anchor would send the client
back to the list for the one number it needs to draw the chips it just tapped.

It is not an aggregate, not a port and not a schema — a read model one field
wider than the aggregate, which is why it lives in the application layer and
imports nothing from the presentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.kernel import Instant
from app.modules.plans.domain.plan import Plan


@final
@dataclass(frozen=True, slots=True)
class PlanRow:
    """One court's plan, written or not, beside the anchor it is measured from."""

    plan: Plan
    anchor: Instant


__all__ = ["PlanRow"]
