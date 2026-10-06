"""The register of what ``games`` demands of other contexts, and who signs it.

**A register of its own rather than rows in another, and that is the rule
rather than a preference.** ``games_demands.py`` holds what this context
*publishes*; this holds what it *demands* of contexts it does not write — the
matcher's answer about a game's court (``docs/adr/0161``), and who the club's
desk checked in to a booked game (#547). A provider's list and a consumer's
list are two kinds of claim, and each register's exhaustiveness assertion is
about its own kind: **a new provider or a new consumer gets a new register, not
a row in somebody else's**, and the first person to add a row should not have
to guess which list it belongs in.

**Two rows, and the tuple is what is asserted over.** A register asserts about
the ports it declares rather than about every ``Protocol`` in
``games/domain/ports.py``: most of them are this context's own reads or what it
publishes, contracted on the register beside this one. ``PlayerNames`` is the
other port this context consumes and is deliberately not here: one field wide,
over ``users``, it is what the games list already exercises on every read and
was never an outward demand on a context with rules of its own.

**A row carries a builder over a session**, the shape every register shares
(``matcher_demands.RegisteredImplementation``): the pairing is read side against
side from the people's Levels (#575), so it asks for nothing but the session,
and each builder is the one the route's own dependency calls — the suite
exercises what ships rather than a second construction of it.

**A port with nothing registered is a red build**, asserted in the suite against
``GAME_DEMANDS``, because a port added in a hurry would otherwise look contracted
while nothing on earth ran against it.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import build_club_check_ins, build_game_court_pairing
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.games.domain.ports import ClubCheckIns, CourtPairing

P = TypeVar("P")

#: What this context asks other contexts for, declared as data for the same
#: reason every other register is: *a port with no registered implementation* has to
#: be a question something can ask.
GAME_DEMANDS: tuple[type, ...] = (CourtPairing, ClubCheckIns)

GAME_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=CourtPairing,
        name="GamesCourtPairing",
        build=build_game_court_pairing,
    ),
    RegisteredImplementation(
        port=ClubCheckIns,
        name="BookingCheckIns",
        build=build_club_check_ins,
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in GAME_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "GAME_DEMANDS",
    "GAME_IMPLEMENTATIONS",
    "implementations_of",
]
