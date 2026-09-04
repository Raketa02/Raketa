"""Audit-trail handler for all six game events.

The outbox carries side effects only, never a state transition a response depends
on — and the side effects this context will grow are the ones that reach the
people in it: *somebody entered a score, look at it before tomorrow*, and
*your result is agreed*. Neither is built, because nothing here can reach a
phone; both belong on a handler here rather than inside the aggregate, which is
why the subscription exists before there is anything interesting on it.

**Nothing here logs a payload.** The payload is four people and what each of them
claims happened; the event name, the moment and the delivery ids answer *did the
write land* without reconstructing somebody's evening from a log aggregator.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


class LogGameEvent:
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
