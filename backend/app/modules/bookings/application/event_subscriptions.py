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

**``bookings.confirmed`` and ``bookings.court_moved`` are at version 2** (#671;
Q122): each gained the court's kind, ``indoor``, a required fact on the wire —
a change to the shape, versioned as one. Version 1 of each is not registered:
the store is reset with the change, so a stored row of it is a decoding error,
and no row of version 2 ever named a court without its kind.

**``bookings.court_moved`` version 2 gained two defaulted facts** (#672): the
club's cancel a move took the place of (``reason``) and the court it left
(``moved_from``). Defaulted, so the version stays and a move recorded before
reads as the club's own — the way ``notifications.notice_given`` grows.

**A friends game's five names are version 1** (#751; ``docs/adr/0202`` §5):
``bookings.booked_by_a_friend`` — the Booking's second birth, court kind and
all — and its invited seats' ``…invited_seat_accepted``, ``…invited_seat_declined``
and ``…invited_seat_ran_out``, and ``bookings.called_off_by_the_sender``.

**A friends game's empty seats add four, version 1** (#752): a friend invited
into one, ``bookings.seat_invited``, and that invitation ended because somebody
else took the seat first, ``bookings.invited_seat_taken``; a seat put to the
group, ``bookings.seat_opened``; and the sender warned a day before the
cut-off, ``bookings.cover_warned``. The defaults ``InvitedSeat`` grew are the
fold's, never the wire's: ``bookings.booked_by_a_friend`` is unchanged.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.bookings.application.handlers import (
    LogBookingEvent,
    LogNewBookingsSummary,
)
from app.modules.bookings.domain.events import (
    BookedByAFriend,
    BookingConfirmed,
    CalledOffAtCutOff,
    CalledOffBySender,
    CancelledByClub,
    CardFixed,
    CardToFix,
    CourtMoved,
    CoverWarned,
    InvitedSeatAccepted,
    InvitedSeatDeclined,
    InvitedSeatRanOut,
    InvitedSeatTaken,
    KeptSeatRanOut,
    NewBookingsSummarised,
    PlayerCheckedIn,
    NoSaidToTheSeat,
    SeatInvited,
    SeatKept,
    SeatLeft,
    SeatOpened,
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
    (BookedByAFriend, "bookings.booked_by_a_friend"),
    (InvitedSeatAccepted, "bookings.invited_seat_accepted"),
    (InvitedSeatDeclined, "bookings.invited_seat_declined"),
    (InvitedSeatRanOut, "bookings.invited_seat_ran_out"),
    (CalledOffBySender, "bookings.called_off_by_the_sender"),
    (SeatInvited, "bookings.seat_invited"),
    (InvitedSeatTaken, "bookings.invited_seat_taken"),
    (SeatOpened, "bookings.seat_opened"),
    (CoverWarned, "bookings.cover_warned"),
)


#: The wire version the two events that name a court are written under: a
#: court without its kind was version 1 (#671).
WITH_THE_COURT_S_KIND_VERSION = 2


def register_booking_events(catalog: EventCatalog) -> None:
    for event_class, name in _EVENTS:
        version = (
            WITH_THE_COURT_S_KIND_VERSION
            if event_class in (BookingConfirmed, CourtMoved)
            else 1
        )
        catalog.register(event_class, name=name, version=version)


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
    dispatcher.subscribe(BookedByAFriend, LogBookingEvent())
    dispatcher.subscribe(InvitedSeatAccepted, LogBookingEvent())
    dispatcher.subscribe(InvitedSeatDeclined, LogBookingEvent())
    dispatcher.subscribe(InvitedSeatRanOut, LogBookingEvent())
    dispatcher.subscribe(CalledOffBySender, LogBookingEvent())
    dispatcher.subscribe(SeatInvited, LogBookingEvent())
    dispatcher.subscribe(InvitedSeatTaken, LogBookingEvent())
    dispatcher.subscribe(SeatOpened, LogBookingEvent())
    dispatcher.subscribe(CoverWarned, LogBookingEvent())
    dispatcher.subscribe(NewBookingsSummarised, LogNewBookingsSummary())
