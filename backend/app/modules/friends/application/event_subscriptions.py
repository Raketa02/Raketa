"""The Friends context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to. Eleven names, all at version 1 (``domain/events.py``).

**Four listeners**: the audit line, which needs nothing per delivery; the
block ender (``handlers/blocking.py``) and the answerer of the asks for a level
(``handlers/level_got.py``, on the rating's first level in a sport and on an
ask, #749),
which write and so are subscribed per delivery run over its session
(``app/bootstrap/events.py``); and Notifications' teller, which tells a request,
*friends made*, *level asked* and *level got* — subscribed by Notifications,
which this context does not know.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.blocks.domain.events import PlayerBlocked, PlayerBlockedNamingAScreen
from app.modules.friends.application.handlers import (
    AnswerTheAsksForALevel,
    EndFriendshipsOnABlock,
    LogFriendEvent,
)
from app.modules.friends.domain.events import (
    FriendLinkMade,
    FriendLinkReplaced,
    FriendRequestBroughtBack,
    FriendRequestCancelled,
    FriendRequestCrossed,
    FriendRequested,
    FriendRequestSetAside,
    FriendshipEnded,
    FriendsMade,
    LevelAsked,
    LevelGot,
)
from app.modules.rating.domain.events import RatingInitialised

_CONTRACTS = (
    (FriendRequested, "friends.friend_requested", 1),
    (FriendRequestSetAside, "friends.friend_request_set_aside", 1),
    (FriendRequestCancelled, "friends.friend_request_cancelled", 1),
    (FriendRequestCrossed, "friends.friend_request_crossed", 1),
    (FriendsMade, "friends.friends_made", 1),
    (FriendshipEnded, "friends.friendship_ended", 1),
    (FriendRequestBroughtBack, "friends.friend_request_brought_back", 1),
    (FriendLinkMade, "friends.friend_link_made", 1),
    (FriendLinkReplaced, "friends.friend_link_replaced", 1),
    (LevelAsked, "friends.level_asked", 1),
    (LevelGot, "friends.level_got", 1),
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


def subscribe_the_level_answerer(
    dispatcher: EventDispatcher, answerer: AnswerTheAsksForALevel
) -> None:
    """A friend's level answers every ask for it, in the transaction that
    delivers it (#749): the rating's first level in a sport, and an ask made of
    somebody whose level is already there."""

    dispatcher.subscribe(RatingInitialised, answerer)
    dispatcher.subscribe(LevelAsked, answerer)
