"""The Bookings context's log line, one per event.

A delivered event with no handler is a delivery failure, so each is logged as
every context's are: the booking, and — where the event carries them — its club
and its game. Never who paid what, and never a club's note on a refusal.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.bookings.domain.events import (
    BookingAccepted,
    BookingConfirmed,
    BookingRefused,
    BookingRequested,
    BookingTimedOut,
    RequestWithdrawn,
)

logger = logging.getLogger(__name__)

BookingEvent = (
    BookingConfirmed
    | BookingRequested
    | BookingAccepted
    | BookingRefused
    | BookingTimedOut
    | RequestWithdrawn
)

_NAMES = {
    BookingConfirmed: "bookings.booking.confirmed",
    BookingRequested: "bookings.booking.requested",
    BookingAccepted: "bookings.booking.accepted",
    BookingRefused: "bookings.booking.refused",
    BookingTimedOut: "bookings.booking.timed_out",
    RequestWithdrawn: "bookings.booking.request_withdrawn",
}


class LogBookingEvent:
    async def __call__(self, event: BookingEvent, context: DeliveryContext) -> None:
        extra: dict[str, object] = {
            "booking_id": str(event.booking_id),
            "occurred_at": event.occurred_at.isoformat(),
            "event_id": str(context.event_id),
            "attempt": context.attempt,
        }
        if isinstance(event, (BookingConfirmed, BookingRequested)):
            extra["club_id"] = str(event.club_id)
        if isinstance(event, (BookingConfirmed, BookingAccepted)):
            extra["game_id"] = str(event.game_id)
        logger.info(_NAMES[type(event)], extra=extra)
