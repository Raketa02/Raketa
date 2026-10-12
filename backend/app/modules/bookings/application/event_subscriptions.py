"""The Bookings context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to (``.claude/rules/domain-events.md``).

**``bookings.player_checked_in`` is retired** with desk check-in (#651;
``docs/adr/0195`` §9): nothing writes it, and it stays registered — decode-only,
logged like the rest if a stored row is ever delivered — so a stored row still
decodes, and the Booking's fold reads it and changes nothing.

**On request's seven names are unregistered** with On request (#669;
``docs/adr/0196`` §1): ``bookings.requested``, ``bookings.accepted``,
``bookings.refused``, ``bookings.timed_out``, ``bookings.request_withdrawn``,
``bookings.awaiting_a_payment`` and ``bookings.payment_not_in_time``. The local
store is reset with the removal and only ``local`` has ever run, so a class
kept only so an old row decodes would be a reader for a fact nothing reads.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.bookings.application.handlers import (
    LogBookingEvent,
    LogNewBookingsSummary,
)
from app.modules.bookings.domain.events import (
    BookingConfirmed,
    CalledOffAtCutOff,
    CancelledByClub,
    CardFixed,
    CardToFix,
    CourtMoved,
    KeptSeatRanOut,
    NewBookingsSummarised,
    PlayerCheckedIn,
    NoSaidToTheSeat,
    SeatKept,
    SeatLeft,
    SeatRescued,
)

_EVENTS = (
    (BookingConfirmed, "bookings.confirmed"),
    (SeatLeft, "bookings.seat_left"),
    (CalledOffAtCutOff, "bookings.called_off_at_cut_off"),
    (SeatRescued, "bookings.seat_rescued"),
    (NoSaidToTheSeat, "bookings.no_said_to_the_seat"),
    (CourtMoved, "bookings.court_moved"),
    (CancelledByClub, "bookings.cancelled_by_club"),
    (PlayerCheckedIn, "bookings.player_checked_in"),
    (NewBookingsSummarised, "bookings.new_bookings_summarised"),
    (CardToFix, "bookings.card_to_fix"),
    (CardFixed, "bookings.card_fixed"),
    (SeatKept, "bookings.seat_kept"),
    (KeptSeatRanOut, "bookings.kept_seat_ran_out"),
)


def register_booking_events(catalog: EventCatalog) -> None:
    for event_class, name in _EVENTS:
        catalog.register(event_class, name=name, version=1)


def subscribe_booking_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(BookingConfirmed, LogBookingEvent())
    dispatcher.subscribe(SeatLeft, LogBookingEvent())
    dispatcher.subscribe(CalledOffAtCutOff, LogBookingEvent())
    dispatcher.subscribe(SeatRescued, LogBookingEvent())
    dispatcher.subscribe(NoSaidToTheSeat, LogBookingEvent())
    dispatcher.subscribe(CourtMoved, LogBookingEvent())
    dispatcher.subscribe(CancelledByClub, LogBookingEvent())
    dispatcher.subscribe(PlayerCheckedIn, LogBookingEvent())
    dispatcher.subscribe(CardToFix, LogBookingEvent())
    dispatcher.subscribe(CardFixed, LogBookingEvent())
    dispatcher.subscribe(SeatKept, LogBookingEvent())
    dispatcher.subscribe(KeptSeatRanOut, LogBookingEvent())
    dispatcher.subscribe(NewBookingsSummarised, LogNewBookingsSummary())
