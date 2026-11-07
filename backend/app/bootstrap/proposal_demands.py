"""The register of what ``proposals`` demands of other contexts for Home and a
game's details (#542), and who signs each demand.

**A register of its own**, on the rule every register here states: a new
consumer gets a new register, not a row in somebody else's. **Seventeen rows,
and the tuple is what is asserted over**: a player's booked games (``bookings``),
where each booked game's result stands (``games``), how far a club is from a
player (the Player profile and ``clubs``), what each player is called on a
club's bookings (``users``) — and, for leaving and the cut-off (#544), what
happens to a booked game after the fill (``bookings``), a paid share given back
and what a late leaver would get back (``payments``, #641) — and, for posting
(#546), whether two people may share a court and the window a player's Level
makes (the matcher's pair rule over blocks, the Player profile and rating) and
each member's Level, week, gender and preference (rating and the Player
profile) — and, for the club running its bookings (#547), a club's bookings as
its desk reads and runs them (``bookings``), what each took and gave back
(``payments``) and the group each pool is (``groups``) — and, for the kind of
court a card promises (#671), the kinds of the free courts at a club and hour
(``clubs``) — and, for the friends card (#750), every hour a club sells with its
free courts named in the club's order (``clubs``, ``CourtHours`` — the first of
the proposer's ports to get its row) — and, for a friends game (#751), the game
booked at send, its invited seats answered and called off by its sender
(``bookings``, ``FriendsGameBookings``) and each cover taken or let go at the
cut-off (``payments``, ``CoversAtTheCutOff``) — each a fact another context
owns, read through a port declared in this context's words. The sender's court
held at send (``SendersCourts``) asks the provider, and is contracted over HTTP
with the fake.

**Not yet the whole of the context's demands.** The rest of the deck's, the
proposer's and the fill's ports (#538–#541) were contracted over HTTP and never
registered; they belong on this list, and the first ticket to touch one adds its
row here — as posting (#546) did for ``PlayerFit`` and ``PlayersInPlay``.

**A row carries a builder over a session**, as the conversation register's do.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_booked_game_changes,
    build_booking_takings,
    build_late_refunds,
    build_club_bookings,
    build_pool_origins,
    build_club_distances,
    build_game_results,
    build_cards_to_fix,
    build_checked_shares,
    build_fake_payments,
    build_held_shares,
    build_holding_times,
    build_player_bookings,
    build_player_fit,
    build_players_in_play,
    build_proposal_player_names,
    build_seat_refunds,
    build_court_hours,
    build_court_kinds,
    build_clock,
    build_friend_requests_on_home,
    build_reader_relations,
    build_friends_game_bookings,
    build_covers_at_the_cut_off,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.core.config import get_settings
from app.modules.proposals.domain.ports import (
    CoversAtTheCutOff,
    FriendsGameBookings,
    BookedGameChanges,
    BookingTakings,
    LateRefunds,
    ClubBookings,
    ClubDistances,
    GameResults,
    CardsToFix,
    CheckedShares,
    CourtHours,
    CourtKinds,
    HeldShares,
    HoldingTimes,
    PlayerBookings,
    PlayerFit,
    PlayerNames,
    PlayersInPlay,
    PoolOrigins,
    SeatRefunds,
    ReaderRelations,
    FriendRequestsOnHome,
)

P = TypeVar("P")

#: What Home and the details ask of the rest of the platform, declared as data
#: so that *a port with no registered implementation* is a question something
#: can ask.
PROPOSAL_DEMANDS: tuple[type, ...] = (
    PlayerBookings,
    GameResults,
    ClubDistances,
    PlayerNames,
    BookedGameChanges,
    SeatRefunds,
    HeldShares,
    CheckedShares,
    CardsToFix,
    HoldingTimes,
    LateRefunds,
    PlayerFit,
    PlayersInPlay,
    ClubBookings,
    BookingTakings,
    PoolOrigins,
    CourtKinds,
    CourtHours,
    ReaderRelations,
    FriendRequestsOnHome,
    FriendsGameBookings,
    CoversAtTheCutOff,
)


PROPOSAL_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=FriendsGameBookings,
        name="BookingsFriendsGameBookings",
        build=build_friends_game_bookings,
    ),
    RegisteredImplementation(
        port=CoversAtTheCutOff,
        name="PaymentsCoversAtTheCutOff",
        build=build_covers_at_the_cut_off,
    ),
    RegisteredImplementation(
        port=PlayerBookings,
        name="BookingsPlayerBookings",
        build=build_player_bookings,
    ),
    RegisteredImplementation(
        port=CourtKinds,
        name="SellableCourtKinds",
        build=build_court_kinds,
    ),
    RegisteredImplementation(
        port=CourtHours,
        name="ClubCourtHours",
        build=build_court_hours,
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
        port=HeldShares,
        name="PaymentsHeldShares",
        build=lambda session: build_held_shares(session),
    ),
    RegisteredImplementation(
        port=CheckedShares,
        name="PaymentsCheckedShares",
        # A fresh fake of the run's own: what is due, and a holding of nothing
        # due, ask the provider nothing.
        build=lambda session: build_checked_shares(
            session, provider=build_fake_payments(), settings=get_settings()
        ),
    ),
    RegisteredImplementation(
        port=CardsToFix,
        name="PaymentsCardsToFix",
        build=lambda session: build_cards_to_fix(session),
    ),
    RegisteredImplementation(
        port=HoldingTimes,
        name="PaymentsHoldingTimes",
        build=lambda session: build_holding_times(session),
    ),
    RegisteredImplementation(
        port=LateRefunds,
        name="PaymentsLateRefunds",
        build=build_late_refunds,
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
        build=build_club_bookings,
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
        port=ReaderRelations,
        name="FriendsReaderRelations",
        build=build_reader_relations,
    ),
    RegisteredImplementation(
        port=FriendRequestsOnHome,
        name="FriendsRequestsOnHome",
        build=lambda session: build_friend_requests_on_home(
            session, settings=get_settings(), clock=build_clock()
        ),
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
