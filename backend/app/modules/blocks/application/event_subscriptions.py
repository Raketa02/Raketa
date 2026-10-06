"""The Blocks context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to: renaming ``PlayerBlocked`` must never change what is already in the store.

**Two names, and the roster is closed by ADR-0095 rather than by convenience.**
A third block event would be a third thing a block can be, and the two the record
admits — made and lifted — are the whole of it. If a reason is ever wanted it
arrives as a *Report*, in a context of its own, with durable names of its own.

**``blocks.player_blocked`` is written at version 2, and version 1 still
decodes** (``docs/adr/0193`` §5). v1 named the screen a block was made from, and
dropping a field is a change to the wire shape, so it is versioned as one rather
than an edit. Blocks are a safety record and live streams hold v1 rows, so it is
kept **decode-only** — ``PlayerBlockedNamingAScreen``, which the Block folds as
the same fact — rather than unregistered with a store reset. It hears the audit
line like v2, and Proposals' withdrawal hears both, so an undelivered v1 row
still delivers and still takes the blocker's yeses back. ``blocks.player_unblocked``
stays v1: it never had a surface. Neither will gain a field that could carry
free text.

**The audit line is not the only listener.** Proposals takes back the blocker's
yeses where the blocked person is In (``docs/adr/0193`` §4), subscribed per
delivery run because it writes (``app/bootstrap/events.py``).
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.blocks.application.handlers import LogBlockEvent
from app.modules.blocks.domain.events import (
    PlayerBlocked,
    PlayerBlockedNamingAScreen,
    PlayerUnblocked,
)

#: Each durable name **with the version it is written under** — and the one
#: version only read, beside the one written.
_CONTRACTS = (
    (PlayerBlocked, "blocks.player_blocked", 2),
    (PlayerBlockedNamingAScreen, "blocks.player_blocked", 1),
    (PlayerUnblocked, "blocks.player_unblocked", 1),
)


def register_block_events(catalog: EventCatalog) -> None:
    for event_cls, name, version in _CONTRACTS:
        catalog.register(event_cls, name=name, version=version)


def subscribe_block_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name, _ in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogBlockEvent(name))
