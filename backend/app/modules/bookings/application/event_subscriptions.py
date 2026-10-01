from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.bookings.application.handlers import LogBookingEvent
from app.modules.bookings.domain.events import (
    BookingAccepted,
    BookingConfirmed,
    BookingRefused,
    BookingRequested,
    BookingTimedOut,
    RequestWithdrawn,
)

_EVENTS = (
    (BookingConfirmed, "bookings.confirmed"),
    (BookingRequested, "bookings.requested"),
    (BookingAccepted, "bookings.accepted"),
    (BookingRefused, "bookings.refused"),
    (BookingTimedOut, "bookings.timed_out"),
    (RequestWithdrawn, "bookings.request_withdrawn"),
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
