"""The Friends context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to. Six names, all at version 1 (``domain/events.py``).

**Three listeners**: the audit line, which needs nothing per delivery; the
block ender (``handlers/blocking.py``), which writes and so is subscribed per
delivery run over its session (``app/bootstrap/events.py``); and Notifications'
teller, which tells a request and *friends made* — subscribed by Notifications,
which this context does not know.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.blocks.domain.events import PlayerBlocked, PlayerBlockedNamingAScreen
from app.modules.friends.application.handlers import (
    EndFriendshipsOnABlock,
    LogFriendEvent,
)
from app.modules.friends.domain.events import (
    FriendRequestCancelled,
    FriendRequestCrossed,
    FriendRequested,
    FriendRequestSetAside,
    FriendshipEnded,
    FriendsMade,
)

_CONTRACTS = (
    (FriendRequested, "friends.friend_requested", 1),
    (FriendRequestSetAside, "friends.friend_request_set_aside", 1),
    (FriendRequestCancelled, "friends.friend_request_cancelled", 1),
    (FriendRequestCrossed, "friends.friend_request_crossed", 1),
    (FriendsMade, "friends.friends_made", 1),
    (FriendshipEnded, "friends.friendship_ended", 1),
)


def register_friend_events(catalog: EventCatalog) -> None:
    for event_cls, name, version in _CONTRACTS:
        catalog.register(event_cls, name=name, version=version)


def subscribe_friend_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name, _ in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogFriendEvent(name))


def subscribe_the_block_ender(
    dispatcher: EventDispatcher, ender: EndFriendshipsOnABlock
) -> None:
    """A block ends a friendship in the transaction that delivers it — **both
    versions of a block**, as Proposals' withdrawal hears them."""

    dispatcher.subscribe(PlayerBlocked, ender)
    dispatcher.subscribe(PlayerBlockedNamingAScreen, ender)
