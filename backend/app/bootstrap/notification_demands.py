"""The register of what ``notifications`` demands of contexts it does not write
(#549).

**A register of its own**, on the rule every register here states: a new
consumer gets a new register. Notifications is *told* through the outbox and
tells nothing (``.importlinter``'s *No context knows Notifications exists*), so
it publishes no port and has no provider register; every row here is a
demand — what a game is now (``GameBriefs``: the proposal's stream and its
booking's), what its court says (``GameCourts``: the Game's own stream, #663),
which booked hours have just ended (``EndedHours``: the bookings' projection),
whose deck shows a card and the kind of court it promises (``Decks``: the deck's
own ``shows`` and ``kind_of_court``, #673), what
a refund gave back (``PaidShares``: the share's Seat charge),
who an open seat is offered to (``SeatOffers``: the Fill in board's own offer)
and what a person and a club are called (``Names``) — and, for *Get your level*
(#727), when each account first joined a group it is in now (``GroupJoiners``:
the groups' own directory) and who holds a rating (``RatedAccounts``: rating's
published read). Each is signed in ``notifications/infrastructure/told_by.py``.

**The deck behind** ``Decks.showing`` **and the offer behind**
``SeatOffers.offered_among`` **are Proposals' own** — ``ReadGroupDeck`` and
``RescueOffers`` — and are driven whole over HTTP where they are written; here
they are read through, and ``tests/api/test_notifications.py`` drives them for
the alerts.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_game_courts,
    build_decks,
    build_ended_hours,
    build_game_briefs,
    build_group_joiners,
    build_notice_names,
    build_paid_shares,
    build_rated_accounts,
    build_seat_offers,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.core.config import get_settings
from app.modules.notifications.domain.ports import (
    GameCourts,
    Decks,
    EndedHours,
    GameBriefs,
    GroupJoiners,
    Names,
    PaidShares,
    RatedAccounts,
    SeatOffers,
)

P = TypeVar("P")

#: What Notifications asks of the rest of the platform, declared as data so that
#: *a port with no registered implementation* is a question something can ask.
NOTIFICATION_DEMANDS: tuple[type, ...] = (
    GameBriefs,
    GameCourts,
    EndedHours,
    Decks,
    PaidShares,
    SeatOffers,
    Names,
    GroupJoiners,
    RatedAccounts,
)


NOTIFICATION_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=GameBriefs, name="BookedAndProposedGames", build=build_game_briefs
    ),
    RegisteredImplementation(
        port=GameCourts, name="GameStreamCourts", build=build_game_courts
    ),
    RegisteredImplementation(
        port=EndedHours, name="BookedHours", build=build_ended_hours
    ),
    RegisteredImplementation(
        port=Decks,
        name="ProposalsDecks",
        build=lambda session: build_decks(session, settings=get_settings()),
    ),
    RegisteredImplementation(
        port=PaidShares, name="SeatChargeShares", build=build_paid_shares
    ),
    RegisteredImplementation(
        port=SeatOffers,
        name="RescueSeatOffers",
        build=build_seat_offers,
    ),
    RegisteredImplementation(
        port=Names, name="PlatformNames", build=build_notice_names
    ),
    RegisteredImplementation(
        port=GroupJoiners, name="DirectoryGroupJoiners", build=build_group_joiners
    ),
    RegisteredImplementation(
        port=RatedAccounts, name="RatingsRatedAccounts", build=build_rated_accounts
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in NOTIFICATION_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "NOTIFICATION_DEMANDS",
    "NOTIFICATION_IMPLEMENTATIONS",
    "implementations_of",
]
