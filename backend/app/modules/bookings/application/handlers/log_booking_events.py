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
    CalledOffAtCutOff,
    CancelledByClub,
    CourtMoved,
    PlayerCheckedIn,
    RequestWithdrawn,
    NoSaidToTheSeat,
    SeatLeft,
    SeatRescued,
)

logger = logging.getLogger(__name__)

BookingEvent = (
    BookingConfirmed
    | BookingRequested
    | BookingAccepted
    | BookingRefused
    | BookingTimedOut
    | RequestWithdrawn
    | SeatLeft
    | CalledOffAtCutOff
    | SeatRescued
    | NoSaidToTheSeat
    | CourtMoved
    | CancelledByClub
    | PlayerCheckedIn
)

_NAMES = {
    BookingConfirmed: "bookings.booking.confirmed",
    BookingRequested: "bookings.booking.requested",
    BookingAccepted: "bookings.booking.accepted",
    BookingRefused: "bookings.booking.refused",
    BookingTimedOut: "bookings.booking.timed_out",
    RequestWithdrawn: "bookings.booking.request_withdrawn",
    SeatLeft: "bookings.booking.seat_left",
    CalledOffAtCutOff: "bookings.booking.called_off_at_cut_off",
    SeatRescued: "bookings.booking.seat_rescued",
    NoSaidToTheSeat: "bookings.booking.no_said_to_the_seat",
    CourtMoved: "bookings.booking.court_moved",
    CancelledByClub: "bookings.booking.cancelled_by_club",
    PlayerCheckedIn: "bookings.booking.player_checked_in",
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
