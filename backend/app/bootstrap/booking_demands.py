"""The register of what ``bookings`` demands of other contexts, and who signs
each demand (#543).

**A register of its own**, on the rule every register here states: a new
consumer gets a new register, not a row in somebody else's. **Two rows, and the
tuple is what is asserted over**: which court a club still has for Raketa at an
hour, with its cut-off and its time to confirm, and whom an email to a club is
addressed to — both facts the Club context owns, read through ports declared in
this context's words and signed in ``bookings/infrastructure/``.

**Not yet the whole of the context's demands.** The ordinary Game a booking
opens (``GameOpening``, #541) was contracted over HTTP and never registered; it
belongs on this list, and the first ticket to touch it adds its row here.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import build_club_courts_at_the_hour, build_club_desks
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.bookings.domain.ports import ClubCourtsAtTheHour, ClubDesks

P = TypeVar("P")

#: What the Bookings context asks of the rest of the platform, declared as data
#: so that *a port with no registered implementation* is a question something
#: can ask.
BOOKING_DEMANDS: tuple[type, ...] = (ClubCourtsAtTheHour, ClubDesks)


BOOKING_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=ClubCourtsAtTheHour,
        name="SellableClubCourts",
        build=build_club_courts_at_the_hour,
    ),
    RegisteredImplementation(
        port=ClubDesks,
        name="AccountClubDesks",
        build=build_club_desks,
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in BOOKING_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "BOOKING_DEMANDS",
    "BOOKING_IMPLEMENTATIONS",
    "implementations_of",
]
