from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


class LogFriendEvent:
    """Audit line for every friendship event — **no payload**: who asked whom,
    and who removed or blocked whom, is nothing a log aggregator should hold.
    The name, the moment and the delivery ids answer *did the write land*."""

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
