from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


class LogMatchEvent:
    """Audit-trail handler for every Matches announcement.

    **This is the trail ADR-0034 says is the real cost of the decision.** The
    match keeps no history, so until the planned playerEventsTracker exists the
    only record of *who changed this, and when* is the outbox and whatever
    consumes it — and today that is this. It is a stub in the same sense the
    rating context's is, and it is load-bearing in a way that one is not.

    Real handlers follow the same shape: implement
    ``async __call__(event, context)`` and register at startup.
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
