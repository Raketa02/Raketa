"""``GeneralOrders`` in this process's memory — **the in-memory equivalent**
of the ephemeral store's (#770).

What a test reads through, and what a run with no store of its own keeps its
orders in — a seed run's drain and its screen reads — so the same reads answer
the same way. **Per instance**: two of them are two stores, and an order kept
in one is not held by the other. Forgets are counted as Redis counts them, and
an order kept at an older count is held by nobody.
"""

from __future__ import annotations

from app.kernel import Sport
from app.modules.rankings.domain.general_order import GeneralOrder, OrderInHand
from app.modules.rankings.domain.ports import HeldOrder


class InMemoryGeneralOrders:
    def __init__(self) -> None:
        self._kept: dict[Sport, tuple[int, GeneralOrder]] = {}
        self._forgotten: dict[Sport, int] = {}

    async def held(self, sport: Sport) -> HeldOrder | None:
        kept = self._kept.get(sport)
        if kept is None or kept[0] != self._forgotten.get(sport, 0):
            return None
        return OrderInHand(kept[1])

    async def forgotten(self, sport: Sport) -> int:
        return self._forgotten.get(sport, 0)

    async def keep(self, order: GeneralOrder, *, forgotten: int) -> None:
        self._kept[order.sport] = (forgotten, order)

    async def forget(self, sport: Sport) -> None:
        self._forgotten[sport] = self._forgotten.get(sport, 0) + 1
        self._kept.pop(sport, None)
