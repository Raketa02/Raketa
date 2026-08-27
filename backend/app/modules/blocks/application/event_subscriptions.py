"""The Blocks context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to: renaming ``PlayerBlocked`` must never change what is already in the store.

**Two names, and the roster is closed by ADR-0095 rather than by convenience.**
A third block event would be a third thing a block can be, and the two the record
admits — made and lifted — are the whole of it. If a reason is ever wanted it
arrives as a *Report*, in a context of its own, with durable names of its own.

Both are v1 and neither will gain a field that could carry free text. A field
that genuinely could not be defaulted honestly would be version 2 registered
beside version 1, as everywhere else; there is no such field in prospect here,
which is the point.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.blocks.application.handlers import LogBlockEvent
from app.modules.blocks.domain.events import PlayerBlocked, PlayerUnblocked

_CONTRACTS = (
    (PlayerBlocked, "blocks.player_blocked"),
    (PlayerUnblocked, "blocks.player_unblocked"),
)


def register_block_events(catalog: EventCatalog) -> None:
    for event_cls, name in _CONTRACTS:
        catalog.register(event_cls, name=name, version=1)


def subscribe_block_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogBlockEvent(name))
