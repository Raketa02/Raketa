"""The register of what ``notifications`` demands of contexts it does not write
(#549).

**A register of its own**, on the rule every register here states: a new
consumer gets a new register. Notifications is *told* through the outbox and
tells nothing (``.importlinter``'s *No context knows Notifications exists*), so
it publishes no port and has no provider register; every row here is a
demand — what a game is now (``GameBriefs``: the proposal's stream and its
booking's), whose deck shows a card (``Decks``: the deck's own ``shows``), what
a refund gave back (``PaidShares``: the share's Seat charge),
who an open seat is offered to (``SeatOffers``: the Fill in board's own offer)
and what a person and a club are called (``Names``). Each is signed in
``notifications/infrastructure/told_by.py``.

**The deck behind** ``Decks.showing`` **and the offer behind**
``SeatOffers.offered_among`` **are Proposals' own** — ``ReadGroupDeck`` and
``RescueOffers`` — and are driven whole over HTTP where they are written; here
they are read through, and ``tests/api/test_notifications.py`` drives them for
the alerts.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_decks,
    build_game_briefs,
    build_notice_names,
    build_paid_shares,
    build_seat_offers,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.core.config import get_settings
from app.modules.notifications.domain.ports import (
    Decks,
    GameBriefs,
    Names,
    PaidShares,
    SeatOffers,
)

P = TypeVar("P")

#: What Notifications asks of the rest of the platform, declared as data so that
#: *a port with no registered implementation* is a question something can ask.
NOTIFICATION_DEMANDS: tuple[type, ...] = (
    GameBriefs,
    Decks,
    PaidShares,
    SeatOffers,
    Names,
)


NOTIFICATION_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=GameBriefs, name="BookedAndProposedGames", build=build_game_briefs
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
