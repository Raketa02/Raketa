"""The register of what ``proposals`` demands of other contexts for Home and a
game's details (#542), and who signs each demand.

**A register of its own**, on the rule every register here states: a new consumer
gets a new register, not a row in somebody else's. **Five rows, and the tuple is
what is asserted over**: a player's booked games and each seat's check-in code
(``bookings``), where each booked game's result stands (``games``), how far a
club is from a player (the Player profile and ``clubs``), and — for an On request
club (#543) — the request a full game is put to it as and its answer
(``bookings``) and what each player is called on it (``users``) — and, for
leaving and the cut-off (#544), what happens to a booked game after the fill
(``bookings``), a paid share given back and the card fee on one (``payments``)
— each a fact another context owns, read through a port declared in this
context's words.

**Not yet the whole of the context's demands.** The deck's, the proposer's and
the fill's ports (#538–#541) were contracted over HTTP and never registered; they
belong on this list, and the first ticket to touch one adds its row here.

**A row carries a builder over a session**, as the conversation register's do;
the bookings' row also reads the settings, because a check-in code is keyed by
the server's own secret.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_booked_game_changes,
    build_card_fees,
    build_club_distances,
    build_club_requests,
    build_game_results,
    build_player_bookings,
    build_proposal_player_names,
    build_seat_refunds,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.core.config import get_settings
from app.modules.proposals.domain.ports import (
    BookedGameChanges,
    CardFees,
    ClubDistances,
    ClubRequests,
    GameResults,
    PlayerBookings,
    PlayerNames,
    SeatRefunds,
)

P = TypeVar("P")

#: What Home and the details ask of the rest of the platform, declared as data
#: so that *a port with no registered implementation* is a question something
#: can ask.
PROPOSAL_DEMANDS: tuple[type, ...] = (
    PlayerBookings,
    GameResults,
    ClubDistances,
    ClubRequests,
    PlayerNames,
    BookedGameChanges,
    SeatRefunds,
    CardFees,
)


PROPOSAL_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=PlayerBookings,
        name="BookingsPlayerBookings",
        build=lambda session: build_player_bookings(session, settings=get_settings()),
    ),
    RegisteredImplementation(
        port=GameResults,
        name="GamesGameResults",
        build=build_game_results,
    ),
    RegisteredImplementation(
        port=ClubDistances,
        name="ProfileClubDistances",
        build=build_club_distances,
    ),
    RegisteredImplementation(
        port=ClubRequests,
        name="BookingsClubRequests",
        build=lambda session: build_club_requests(session, settings=get_settings()),
    ),
    RegisteredImplementation(
        port=PlayerNames,
        name="UsersPlayerNames",
        build=build_proposal_player_names,
    ),
    RegisteredImplementation(
        port=BookedGameChanges,
        name="BookingsBookedGameChanges",
        build=lambda session: build_booked_game_changes(
            session, settings=get_settings()
        ),
    ),
    RegisteredImplementation(
        port=SeatRefunds,
        name="PaymentsSeatRefunds",
        build=lambda session: build_seat_refunds(session, settings=get_settings()),
    ),
    RegisteredImplementation(
        port=CardFees,
        name="PaymentsCardFees",
        build=lambda session: build_card_fees(),
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in PROPOSAL_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "PROPOSAL_DEMANDS",
    "PROPOSAL_IMPLEMENTATIONS",
    "implementations_of",
]
