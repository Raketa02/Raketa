"""The register of what ``proposals`` demands of other contexts for Home and a
game's details (#542), and who signs each demand.

**A register of its own**, on the rule every register here states: a new consumer
gets a new register, not a row in somebody else's. **Fourteen rows, and the
tuple is what is asserted over**: a player's booked games and each seat's
check-in code (``bookings``), where each booked game's result stands
(``games``), how far a club is from a player (the Player profile and
``clubs``), and — for an On request club (#543) — the request a full game is
put to it as and its answer (``bookings``) and what each player is called on it
(``users``) — and, for
leaving and the cut-off (#544), what happens to a booked game after the fill
(``bookings``), a paid share given back and the card fee on one (``payments``)
— and, for posting (#546), whether two people may share a court and the window
a player's Level makes (the matcher's pair rule over blocks, the Player profile
and rating) and each member's Level, week, gender and preference (rating and
the Player profile) — and, for the club running its bookings (#547), a club's
bookings as its desk reads and runs them (``bookings``), what each took and gave
back (``payments``), the group each pool is (``groups``) and whether a club
checks its players in (``clubs``) — each a fact another context owns, read
through a port declared in this context's words.

**Not yet the whole of the context's demands.** The rest of the deck's, the
proposer's and the fill's ports (#538–#541) were contracted over HTTP and never
registered; they belong on this list, and the first ticket to touch one adds its
row here — as posting (#546) did for ``PlayerFit`` and ``PlayersInPlay``.

**A row carries a builder over a session**, as the conversation register's do;
the bookings' row also reads the settings, because a check-in code is keyed by
the server's own secret.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_booked_game_changes,
    build_booking_takings,
    build_card_fees,
    build_club_bookings,
    build_desk_check_ins,
    build_pool_origins,
    build_club_distances,
    build_club_requests,
    build_game_results,
    build_player_bookings,
    build_player_fit,
    build_players_in_play,
    build_proposal_player_names,
    build_seat_refunds,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.core.config import get_settings
from app.modules.proposals.domain.ports import (
    BookedGameChanges,
    BookingTakings,
    CardFees,
    ClubBookings,
    ClubDistances,
    ClubRequests,
    DeskCheckIns,
    GameResults,
    PlayerBookings,
    PlayerFit,
    PlayerNames,
    PlayersInPlay,
    PoolOrigins,
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
    PlayerFit,
    PlayersInPlay,
    ClubBookings,
    BookingTakings,
    PoolOrigins,
    DeskCheckIns,
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
    RegisteredImplementation(
        port=PlayerFit,
        name="MatcherPlayerFit",
        build=build_player_fit,
    ),
    RegisteredImplementation(
        port=PlayersInPlay,
        name="ProfilePlayersInPlay",
        build=build_players_in_play,
    ),
    RegisteredImplementation(
        port=ClubBookings,
        name="BookingsClubBookings",
        build=lambda session: build_club_bookings(session, settings=get_settings()),
    ),
    RegisteredImplementation(
        port=BookingTakings,
        name="PaymentsBookingTakings",
        build=build_booking_takings,
    ),
    RegisteredImplementation(
        port=PoolOrigins,
        name="GroupPoolOrigins",
        build=build_pool_origins,
    ),
    RegisteredImplementation(
        port=DeskCheckIns,
        name="ClubCourtsDeskCheckIns",
        build=build_desk_check_ins,
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
