"""The Bookings context's log line, one per event.

A delivered event with no handler is a delivery failure, so each is logged as
every context's are: the booking, and — where the event carries them — its club
and its game. Never who paid what.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.bookings.domain.events import (
    BookedByAFriend,
    BookingConfirmed,
    CalledOffAtCutOff,
    CalledOffBySender,
    CoverWarned,
    InvitedSeatAccepted,
    InvitedSeatDeclined,
    InvitedSeatRanOut,
    InvitedSeatTaken,
    SeatInvited,
    SeatOpened,
    CancelledByClub,
    CardFixed,
    CardToFix,
    KeptSeatRanOut,
    NewBookingsSummarised,
    CourtMoved,
    PlayerCheckedIn,
    NoSaidToTheSeat,
    SeatKept,
    SeatLeft,
    SeatRescued,
)

logger = logging.getLogger(__name__)

BookingEvent = (
    BookingConfirmed
    | SeatLeft
    | CalledOffAtCutOff
    | SeatRescued
    | NoSaidToTheSeat
    | CourtMoved
    | CancelledByClub
    | PlayerCheckedIn
    | CardToFix
    | CardFixed
    | SeatKept
    | KeptSeatRanOut
    | BookedByAFriend
    | InvitedSeatAccepted
    | InvitedSeatDeclined
    | InvitedSeatRanOut
    | CalledOffBySender
    | SeatInvited
    | InvitedSeatTaken
    | SeatOpened
    | CoverWarned
)

_NAMES = {
    BookingConfirmed: "bookings.booking.confirmed",
    SeatLeft: "bookings.booking.seat_left",
    CalledOffAtCutOff: "bookings.booking.called_off_at_cut_off",
    SeatRescued: "bookings.booking.seat_rescued",
    NoSaidToTheSeat: "bookings.booking.no_said_to_the_seat",
    CourtMoved: "bookings.booking.court_moved",
    CancelledByClub: "bookings.booking.cancelled_by_club",
    PlayerCheckedIn: "bookings.booking.player_checked_in",
    CardToFix: "bookings.booking.card_to_fix",
    CardFixed: "bookings.booking.card_fixed",
    SeatKept: "bookings.booking.seat_kept",
    KeptSeatRanOut: "bookings.booking.kept_seat_ran_out",
    BookedByAFriend: "bookings.booking.booked_by_a_friend",
    InvitedSeatAccepted: "bookings.booking.invited_seat_accepted",
    InvitedSeatDeclined: "bookings.booking.invited_seat_declined",
    InvitedSeatRanOut: "bookings.booking.invited_seat_ran_out",
    CalledOffBySender: "bookings.booking.called_off_by_the_sender",
    SeatInvited: "bookings.booking.seat_invited",
    InvitedSeatTaken: "bookings.booking.invited_seat_taken",
    SeatOpened: "bookings.booking.seat_opened",
    CoverWarned: "bookings.booking.cover_warned",
}


class LogBookingEvent:
    async def __call__(self, event: BookingEvent, context: DeliveryContext) -> None:
        extra: dict[str, object] = {
            "booking_id": str(event.booking_id),
            "occurred_at": event.occurred_at.isoformat(),
            "event_id": str(context.event_id),
            "attempt": context.attempt,
        }
        if isinstance(event, (BookingConfirmed, BookedByAFriend)):
            extra["club_id"] = str(event.club_id)
            extra["game_id"] = str(event.game_id)
        logger.info(_NAMES[type(event)], extra=extra)


class LogNewBookingsSummary:
    """A club's day summed up: the club and the day, nothing about the games."""

    async def __call__(
        self, event: NewBookingsSummarised, context: DeliveryContext
    ) -> None:
        logger.info(
            "bookings.new_bookings_summarised",
            extra={
                "club_id": str(event.club_id),
                "day": event.day,
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )
