"""The register of what ``bookings`` publishes outward, and who implements it
(#544).

**A provider's register, beside the consumer's** — ``booking_demands.py``
holds what ``bookings`` asks of other contexts; this holds what it answers for
them, exactly as ``games_demands.py`` stands beside ``game_demands.py``. Rows of
both kinds in one list would make each exhaustiveness assertion a claim about
two different things.

**One row**: who kept the booked games they held a seat on, and who broke them
— the *keeps plans* strand's input, read by ``player_score``.

**A port with nothing registered is a red build**, asserted in the suite against
``BOOKINGS_DEMANDS``.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import build_booking_history
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.bookings.domain.ports import BookingHistoryQuery

P = TypeVar("P")

BOOKINGS_DEMANDS: tuple[type, ...] = (BookingHistoryQuery,)


BOOKINGS_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=BookingHistoryQuery,
        name="EventSourcedBookingHistory",
        build=build_booking_history,
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in BOOKINGS_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "BOOKINGS_DEMANDS",
    "BOOKINGS_IMPLEMENTATIONS",
    "implementations_of",
]
