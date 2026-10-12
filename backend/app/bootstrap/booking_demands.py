"""The register of what ``bookings`` demands of other contexts, and who signs
each demand (#543).

**A register of its own**, on the rule every register here states: a new
consumer gets a new register, not a row in somebody else's. **Six rows, and
the tuple is what is asserted over**: which court a club still has for Raketa
at an hour, with its cut-off, the court a club's cancel closes for its hour
(``CourtClosures``, #673), and whom an email to a club is addressed to — all
the Club context's — and the ordinary Game a booking opens
(``GameOpening``, #541, registered by #544, the first ticket to touch it) and
what leaving and the cut-off do to it (``GameChanges``, #544) — the Games
context's — and, since #547, who did not come to that Game (``GameNoShows``),
which the record reads. Each is read through a port declared in this context's
words and signed in ``bookings/infrastructure/``. ``PlayerAddresses``, whom an
On request club's no or silence was emailed to (#623), went with On request
(#669).
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_club_courts_at_the_hour,
    build_club_desks,
    build_court_closures,
    build_game_changes,
    build_game_no_shows,
    build_game_opening,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.bookings.domain.ports import (
    ClubCourtsAtTheHour,
    ClubDesks,
    CourtClosures,
    GameChanges,
    GameNoShows,
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
    GameNoShows,
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
    RegisteredImplementation(
        port=GameNoShows,
        name="GameNoShowsOnTheRecord",
        build=build_game_no_shows,
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
