from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


class LogRatingEvent:
    """Audit-trail handler for every rating-context event.

    The outbox carries side effects only — projections, analytics, later
    notifications — never a state transition a response depends on. Until those
    land this stub keeps the audit trail; real handlers follow the same shape:
    implement `async __call__(event, context)` and register at startup.
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
