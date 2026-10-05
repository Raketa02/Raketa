"""The subscriber that withdraws a leaver's yeses — see ``leaving.py``.

Two ways out of a group: leaving it, and deleting it — which only an Owner alone
in it can do, and which takes their pool's yeses with it the same way.
"""

from __future__ import annotations

from app.application.events import DeliveryContext
from app.kernel import instant
from app.modules.groups.domain.events import GroupDeleted, GroupLeft
from app.modules.proposals.application.leaving import WithdrawALeaversYeses


class WithdrawYesesOnLeaving:
    def __init__(self, withdraw: WithdrawALeaversYeses) -> None:
        self._withdraw = withdraw

    async def __call__(
        self, event: GroupLeft | GroupDeleted, context: DeliveryContext
    ) -> None:
        # A group's pool is filed under the group's own id.
        await self._withdraw.execute(
            pool_id=event.group_id,
            player_id=(
                event.player_id if isinstance(event, GroupLeft) else event.deleted_by
            ),
            at=instant(event.occurred_at),
        )
