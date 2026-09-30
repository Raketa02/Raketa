"""The Payments context's log line, one per event.

A delivered event with no handler is a delivery failure, so each is logged as
every context's are. **The line carries the player and nothing about the card**
— not its brand, its last four digits, a provider id or the address the terms
were accepted from: the ids say whose stream moved, and the stream says the rest
to whoever may read it.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.payments.domain.events import (
    PaymentMethodChanged,
    PaymentMethodRemoved,
    PaymentMethodSaved,
    PaymentMethodUpdated,
    PaymentSetupStarted,
    PaymentTermsAccepted,
)

logger = logging.getLogger(__name__)

PaymentEvent = (
    PaymentSetupStarted
    | PaymentTermsAccepted
    | PaymentMethodSaved
    | PaymentMethodChanged
    | PaymentMethodRemoved
    | PaymentMethodUpdated
)

_LINES: dict[type, str] = {
    PaymentSetupStarted: "payments.setup.started",
    PaymentTermsAccepted: "payments.terms.accepted",
    PaymentMethodSaved: "payments.method.saved",
    PaymentMethodChanged: "payments.method.changed",
    PaymentMethodRemoved: "payments.method.removed",
    PaymentMethodUpdated: "payments.method.updated",
}


class LogPaymentEvent:
    async def __call__(self, event: PaymentEvent, context: DeliveryContext) -> None:
        logger.info(
            _LINES[type(event)],
            extra={
                "player_id": str(event.player_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )
