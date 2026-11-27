"""The register of what ``bookings`` demands of other contexts, and who signs
each demand (#543).

**A register of its own**, on the rule every register here states: a new
consumer gets a new register, not a row in somebody else's. **Five rows, and the
tuple is what is asserted over**: which court a club still has for Rakieta at an
hour, with its cut-off, the court a club's cancel closes for its hour
(``CourtClosures``, #673), and whom an email to a club is addressed to — all the
Club context's — and the ordinary Game a booking opens (``GameOpening``, #541,
registered by #544, the first ticket to touch it) and what leaving and the cut-off
do to it (``GameChanges``, #544) — the Games context's. Each is read through a port
declared in this context's words and signed in ``bookings/infrastructure/``.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_club_courts_at_the_hour,
    build_club_desks,
    build_court_closures,
    build_game_changes,
    build_game_opening,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.bookings.domain.ports import (
    ClubCourtsAtTheHour,
    ClubDesks,
    CourtClosures,
    GameChanges,
    GameOpening,
)

P = TypeVar("P")

#: What the Bookings context asks of the rest of the platform, declared as data
#: so that *a port with no registered implementation* is a question something
#: can ask.
BOOKING_DEMANDS: tuple[type, ...] = (
    ClubCourtsAtTheHour,
    CourtClosures,
    ClubDesks,
    GameOpening,
    GameChanges,
)


BOOKING_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=ClubCourtsAtTheHour,
        name="SellableClubCourts",
        build=build_club_courts_at_the_hour,
    ),
    RegisteredImplementation(
        port=CourtClosures,
        name="ClosedByTheCancel",
        build=build_court_closures,
    ),
    RegisteredImplementation(
        port=ClubDesks,
        name="AccountClubDesks",
        build=build_club_desks,
    ),
    RegisteredImplementation(
        port=GameOpening,
        name="OpenTheGame",
        build=build_game_opening,
    ),
    RegisteredImplementation(
        port=GameChanges,
        name="LeaveAndCallOffTheGame",
        build=build_game_changes,
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
