"""**A block ends a friendship** (``docs/adr/0202`` §2; ADR-0193 §2's one more
reach): whoever of the two blocked the other, their friendship and any open
request between them end, silently, in the transaction that delivers the
block.

**Owed by the block being recorded**, as Proposals' withdrawal is: a block
lifted before its delivery still ends what stood, and unblocking brings nothing
back. Both versions of ``blocks.player_blocked`` are heard — a v1 row not
delivered yet was still a block.

**No commit**: the transaction is the delivery's.
"""

from __future__ import annotations

from typing import final

from app.application.events import DeliveryContext
from app.kernel import instant
from app.modules.blocks.domain.events import PlayerBlocked, PlayerBlockedNamingAScreen
from app.modules.friends.domain.ports import FriendshipRepository
from app.shared.domain import DomainEvent


@final
class EndFriendshipsOnABlock:
    def __init__(self, friendships: FriendshipRepository) -> None:
        self._friendships = friendships

    async def __call__(self, event: DomainEvent, context: DeliveryContext) -> None:
        if not isinstance(event, (PlayerBlocked, PlayerBlockedNamingAScreen)):
            return
        if event.blocker_id == event.blocked_id:
            return
        friendship = await self._friendships.load(event.blocker_id, event.blocked_id)
        friendship.end_by_a_block(
            blocker=event.blocker_id, at=instant(event.occurred_at)
        )
        await self._friendships.save(friendship)
