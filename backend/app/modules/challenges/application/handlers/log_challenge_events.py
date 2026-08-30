"""Audit-trail handler for all six challenge events.

The outbox carries side effects only, never a state transition a response depends
on — and the side effect this context will grow is the one that reaches the
people in it: a notification per invitation, and one per acceptance. Neither is
built, and both belong on a handler here rather than inside the send, which is
why the subscription exists before there is anything interesting on it.

**Nothing here logs a payload.** The payload is a court full of people and what
each of them decided; the event name, the moment and the delivery ids answer *did
the write land* without reconstructing who asked whom from a log aggregator.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


class LogChallengeEvent:
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
