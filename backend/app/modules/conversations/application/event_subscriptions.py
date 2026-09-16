"""The Conversation context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to: renaming ``MessageSent`` must never change what is already in the store.

**Four names, on one aggregate**, and only two of them are entries. The opening
and the game are state this room folds and nothing renders; the message and the
system line are the stream.

**No name here says a room has ended.** The lifetime is derived — off the room's
own stream for a room with a game, off its challenge for one without
(``docs/adr/0153``, ``docs/adr/0164`` §6) — and a durable *closed* would be a
second place for it to be true — the one a subscriber would believe for the whole
gap between an instant passing and a sweep running.

**Two subscriptions, and they are subscriptions of different kinds.** The log
handler below is registered once for the process, like every other context's.
The **teller** — the handler that turns ``challenges``' and ``games``' events into
rooms and lines — is registered per delivery batch, over that batch's session, in
``app/bootstrap/events.py``: it writes, and what it writes has to commit with the
outbox row that told it to.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.conversations.application.handlers import LogConversationEvent
from app.modules.conversations.application.tell_the_room import TellTheRoom
from app.modules.conversations.application.telling import TOLD_ABOUT
from app.modules.conversations.domain.events import (
    ConversationOpened,
    GameNoted,
    MessageSent,
    SystemLineRecorded,
)

_CONTRACTS = (
    (ConversationOpened, "conversations.opened"),
    (GameNoted, "conversations.game_noted"),
    (MessageSent, "conversations.message_sent"),
    (SystemLineRecorded, "conversations.system_line_recorded"),
)


def register_conversation_events(catalog: EventCatalog) -> None:
    for event_cls, name in _CONTRACTS:
        catalog.register(event_cls, name=name, version=1)


def subscribe_conversation_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogConversationEvent(name))


def subscribe_the_room_teller(dispatcher: EventDispatcher, teller: TellTheRoom) -> None:
    """Subscribe one teller to everything this room is told about.

    **Told is a longer list than drawn.** Five events write no line and are
    subscribed anyway: the mutual opening *is* the opening, the planned game is
    where the room learns which game it is about, and the withdrawal, the
    court's call-off and the game's are what destroy the room. ``telling.py``
    is the table, and it is the only place either list is written.
    """

    for event_cls in TOLD_ABOUT:
        dispatcher.subscribe(event_cls, teller)
