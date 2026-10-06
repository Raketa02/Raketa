"""The subscriber that takes back a blocker's yeses — see ``blocking.py``."""

from __future__ import annotations

from app.application.events import DeliveryContext
from app.kernel import instant
from app.modules.blocks.domain.events import PlayerBlocked, PlayerBlockedNamingAScreen
from app.modules.proposals.application.blocking import WithdrawABlockersYeses


class WithdrawYesesOnBlocking:
    def __init__(self, withdraw: WithdrawABlockersYeses) -> None:
        self._withdraw = withdraw

    async def __call__(
        self,
        event: PlayerBlocked | PlayerBlockedNamingAScreen,
        context: DeliveryContext,
    ) -> None:
        await self._withdraw.execute(
            blocker_id=event.blocker_id,
            blocked_id=event.blocked_id,
            at=instant(event.occurred_at),
        )
