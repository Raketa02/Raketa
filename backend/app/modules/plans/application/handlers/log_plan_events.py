"""Audit-trail handler for the three plan events.

The outbox carries side effects only, and this context's one real subscriber is
somebody else's: a room writes a system line for each of these, through a context
that does not know this one exists. What is here is the same audit line every
other context has, so *did the write land* is answerable without asking the room.

**Nothing here logs a payload.** The payload is where four people are meeting and
when — a note between them — and the event name, the moment and the delivery ids
answer the operational question without reassembling somebody's evening out of a
log aggregator. That is the same rule ``games`` keeps about a score, applied to
the one value in this platform that is deliberately unstructured.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


class LogPlanEvent:
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
