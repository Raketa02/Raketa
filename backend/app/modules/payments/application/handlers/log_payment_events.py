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
    ClubPayoutDecided,
    ClubPayoutSent,
    PaymentMethodChanged,
    PaymentMethodRemoved,
    PaymentMethodSaved,
    PaymentMethodUpdated,
    PaymentSetupStarted,
    PaymentTermsAccepted,
    SeatChargeAuthorised,
    SeatChargeCancelled,
    SeatChargeCaptured,
    SeatChargeConfirmed,
    SeatChargeFailed,
    SeatChargeFeeReported,
    SeatChargeRefundDecided,
    SeatChargeRefunded,
    SeatChargeReleased,
    SeatChargeTaken,
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


SeatChargeEvent = (
    SeatChargeAuthorised
    | SeatChargeFailed
    | SeatChargeConfirmed
    | SeatChargeTaken
    | SeatChargeReleased
    | SeatChargeCaptured
    | SeatChargeCancelled
    | SeatChargeFeeReported
    | SeatChargeRefundDecided
    | SeatChargeRefunded
)

_SEAT_CHARGE_LINES: dict[type, str] = {
    SeatChargeAuthorised: "payments.seat_charge.authorised",
    SeatChargeFailed: "payments.seat_charge.failed",
    SeatChargeConfirmed: "payments.seat_charge.confirmed",
    SeatChargeTaken: "payments.seat_charge.taken",
    SeatChargeReleased: "payments.seat_charge.released",
    SeatChargeCaptured: "payments.seat_charge.captured",
    SeatChargeCancelled: "payments.seat_charge.cancelled",
    SeatChargeFeeReported: "payments.seat_charge.fee_reported",
    SeatChargeRefundDecided: "payments.seat_charge.refund_decided",
    SeatChargeRefunded: "payments.seat_charge.refunded",
}


class LogSeatChargeEvent:
    """A seat charge's line: whose share, which charge — never the amount, the
    payment's id at the provider or why a bank refused it."""

    async def __call__(
        self, event: SeatChargeEvent, context: DeliveryContext
    ) -> None:
        logger.info(
            _SEAT_CHARGE_LINES[type(event)],
            extra={
                "charge_id": str(event.charge_id),
                "player_id": str(event.player_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )


ClubPayoutEvent = ClubPayoutDecided | ClubPayoutSent

_CLUB_PAYOUT_LINES: dict[type, str] = {
    ClubPayoutDecided: "payments.club_payout.decided",
    ClubPayoutSent: "payments.club_payout.sent",
}


class LogClubPayoutEvent:
    """A club's payout: the club and the payout, nothing about the amount."""

    async def __call__(self, event: ClubPayoutEvent, context: DeliveryContext) -> None:
        logger.info(
            _CLUB_PAYOUT_LINES[type(event)],
            extra={
                "payout_id": str(event.payout_id),
                "club_id": str(event.club_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )
