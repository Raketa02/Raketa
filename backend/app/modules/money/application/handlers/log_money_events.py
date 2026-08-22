from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


class LogMoneyEvent:
    """Audit-trail handler for every Money announcement.

    The same stub the other three contexts have, and the same shape: implement
    ``async __call__(event, context)`` and register at startup.

    It is worth less here than it is in Matches, and for the opposite reason.
    Matches keeps no history, so its outbox trail *is* the record of who changed
    what; a ledger's history is the ledger, so nothing about a movement is only
    knowable from this line. What the announcement is for is everybody else — a
    reconciliation alert, a receipt, a provider webhook being matched up — none
    of which exists yet.
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
