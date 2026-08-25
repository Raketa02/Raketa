from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


class LogPlayerProfileEvent:
    """Audit-trail handler for every Player profile event.

    The outbox carries side effects only — the ``player_profiles`` read model
    ADR-0089 describes, analytics, later notifications — never a state
    transition a response depends on. Until those land this stub keeps the audit
    trail; real handlers follow the same shape.

    **Nothing here logs a payload**, which matters more in this context than in
    the others: an availability grid is classified as data nobody may see as a
    calendar, and a location is a place a person goes. The event name, the
    moment and the delivery ids are all that is written.
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
