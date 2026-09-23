"""Audit-trail handler for the four conversation events.

**Nothing here logs a payload.** The payload is what people said to each other;
the event name, the moment and the delivery ids answer *did the write land*
without putting a room's contents in a log aggregator. That rule is stronger here
than anywhere else it is written in this repository, because this is the only
context whose payload is somebody's own words.

The subscription exists before there is anything interesting on it for the reason
every other context's does — and here the interesting thing is already known: the
live channel's nudge (``docs/adr/0147`` §3) is a handler on these events, and it
lands beside this one rather than inside the append.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


class LogConversationEvent:
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
