from __future__ import annotations

from app.application.events import DeliveryContext
from app.kernel import instant
from app.modules.games.domain.events import ResultAccepted
from app.modules.rating.application.settle_results import SettleRatingsOnResults


class SettleRatingsOnAnAgreement:
    """*That's right* settles a result at once (#654; ``docs/adr/0195`` §5), so
    its delivery settles that game for rating — **as it stood at the tap**, in
    the delivery's own transaction. Idempotent: a game already folded into a
    rating is stepped over, by this and by the catch-up alike."""

    def __init__(self, settle: SettleRatingsOnResults) -> None:
        self._settle = settle

    async def __call__(self, event: ResultAccepted, context: DeliveryContext) -> None:
        await self._settle.settle(event.game_id, at=instant(event.occurred_at))
