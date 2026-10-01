"""The Bookings context's log line, one per event.

A delivered event with no handler is a delivery failure, so each is logged as
every context's are: the booking, its club and its game — never who paid what.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.bookings.domain.events import BookingConfirmed

logger = logging.getLogger(__name__)


class LogBookingEvent:
    async def __call__(self, event: BookingConfirmed, context: DeliveryContext) -> None:
        logger.info(
            "bookings.booking.confirmed",
            extra={
                "booking_id": str(event.booking_id),
                "club_id": str(event.club_id),
                "game_id": str(event.game_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )
