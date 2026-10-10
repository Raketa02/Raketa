from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.bookings.application.handlers import (
    LogBookingEvent,
    LogNewBookingsSummary,
)
from app.modules.bookings.domain.events import (
    BookingAccepted,
    BookingAwaitingAPayment,
    BookingConfirmed,
    BookingRefused,
    BookingRequested,
    BookingTimedOut,
    CalledOffAtCutOff,
    CancelledByClub,
    CourtMoved,
    NewBookingsSummarised,
    PaymentNotInTime,
    PlayerCheckedIn,
    RequestWithdrawn,
    NoSaidToTheSeat,
    SeatLeft,
    SeatRescued,
)

_EVENTS = (
    (BookingConfirmed, "bookings.confirmed"),
    (BookingRequested, "bookings.requested"),
    (BookingAccepted, "bookings.accepted"),
    (BookingRefused, "bookings.refused"),
    (BookingTimedOut, "bookings.timed_out"),
    (RequestWithdrawn, "bookings.request_withdrawn"),
    (SeatLeft, "bookings.seat_left"),
    (CalledOffAtCutOff, "bookings.called_off_at_cut_off"),
    (SeatRescued, "bookings.seat_rescued"),
    (NoSaidToTheSeat, "bookings.no_said_to_the_seat"),
    (CourtMoved, "bookings.court_moved"),
    (CancelledByClub, "bookings.cancelled_by_club"),
    (PlayerCheckedIn, "bookings.player_checked_in"),
    (NewBookingsSummarised, "bookings.new_bookings_summarised"),
    (BookingAwaitingAPayment, "bookings.awaiting_a_payment"),
    (PaymentNotInTime, "bookings.payment_not_in_time"),
)


def register_booking_events(catalog: EventCatalog) -> None:
    for event_class, name in _EVENTS:
        catalog.register(event_class, name=name, version=1)


def subscribe_booking_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(BookingConfirmed, LogBookingEvent())
    dispatcher.subscribe(BookingRequested, LogBookingEvent())
    dispatcher.subscribe(BookingAccepted, LogBookingEvent())
    dispatcher.subscribe(BookingRefused, LogBookingEvent())
    dispatcher.subscribe(BookingTimedOut, LogBookingEvent())
    dispatcher.subscribe(RequestWithdrawn, LogBookingEvent())
    dispatcher.subscribe(SeatLeft, LogBookingEvent())
    dispatcher.subscribe(CalledOffAtCutOff, LogBookingEvent())
    dispatcher.subscribe(SeatRescued, LogBookingEvent())
    dispatcher.subscribe(NoSaidToTheSeat, LogBookingEvent())
    dispatcher.subscribe(CourtMoved, LogBookingEvent())
    dispatcher.subscribe(CancelledByClub, LogBookingEvent())
    dispatcher.subscribe(PlayerCheckedIn, LogBookingEvent())
    dispatcher.subscribe(BookingAwaitingAPayment, LogBookingEvent())
    dispatcher.subscribe(PaymentNotInTime, LogBookingEvent())
    dispatcher.subscribe(NewBookingsSummarised, LogNewBookingsSummary())
