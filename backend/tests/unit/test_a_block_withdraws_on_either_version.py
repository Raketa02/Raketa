"""A recorded block takes back the blocker's yeses whichever version it was
written under (``docs/adr/0193`` §4–§5).

``blocks.player_blocked`` is written at v2 and v1 still decodes. A v1 row the
outbox has not delivered yet is still a block that was recorded, and what it is
owed — the blocker's yeses where the blocked player is In — does not depend on
the version it was written at.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.application.events import EventDispatcher
from app.application.events.envelope import DeliveryContext
from app.kernel import instant
from app.modules.blocks.domain.events import PlayerBlocked, PlayerBlockedNamingAScreen
from app.modules.proposals.application.event_subscriptions import (
    subscribe_the_blocker,
)
from app.shared.ids import new_uuid

OLA, KUBA = new_uuid(), new_uuid()
AT = datetime(2026, 10, 5, 6, 0, tzinfo=timezone.utc)


class Withdraw:
    def __init__(self) -> None:
        self.asked: list[tuple] = []

    async def execute(self, *, blocker_id, blocked_id, at) -> int:
        self.asked.append((blocker_id, blocked_id, at))
        return 0


async def test_both_versions_of_a_block_take_the_yeses_back():
    withdraw = Withdraw()
    dispatcher = EventDispatcher()
    subscribe_the_blocker(dispatcher, withdraw)  # type: ignore[arg-type]
    context = DeliveryContext(event_id=new_uuid(), attempt=1, occurred_at=AT)

    for event in (
        PlayerBlocked(blocker_id=OLA, blocked_id=KUBA, occurred_at=AT),
        PlayerBlockedNamingAScreen(
            blocker_id=OLA, blocked_id=KUBA, surface="DECK", occurred_at=AT
        ),
    ):
        for handler in dispatcher.subscribers_of(type(event)):
            await handler(event, context)

    assert withdraw.asked == [(OLA, KUBA, instant(AT))] * 2
