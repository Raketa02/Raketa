from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.bookings.application.handlers import LogBookingEvent
from app.modules.bookings.domain.events import BookingConfirmed

_EVENTS = ((BookingConfirmed, "bookings.confirmed"),)


def register_booking_events(catalog: EventCatalog) -> None:
    for event_class, name in _EVENTS:
        catalog.register(event_class, name=name, version=1)


def subscribe_booking_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(BookingConfirmed, LogBookingEvent())
