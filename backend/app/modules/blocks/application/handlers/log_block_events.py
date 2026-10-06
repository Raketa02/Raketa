from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


class LogBlockEvent:
    """Audit-trail handler for both block events.

    The outbox carries side effects only, never a state transition a response
    depends on. **Neither party is notified, in either direction**
    (``docs/adr/0193`` §3); the one side effect a block has is Proposals' —
    taking back the blocker's yeses where the blocked player is In (§4) — and it
    is subscribed there, not here. What a later handler here could legitimately
    be is a moderation read model, and that is a Report's business rather than a
    Block's.

    **Nothing here logs a payload**, which matters more in this context than in
    any other: the payload is two people and the fact that one of them wants
    nothing to do with the other. The event name, the moment and the delivery ids
    are all that is written, which is enough to answer *did the write land* and
    not enough to reconstruct who blocked whom from a log aggregator.
    """

    def __init__(self, name: str) -> None:
        self._name = name

    async def __call__(self, event: DomainEvent, context: DeliveryContext) -> None:
        logger.info(
            self._name,
            extra={
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )
