"""Which screen a block was made from.

``PlayIntentSurface``'s precedent, and it obeys the same rule about what it is
*for*: context recorded beside a fact, never a thing any decision branches on. It
is **client-asserted and a client could lie about it** — accepted for the reason
ADR-0094 accepts it for intent, because the client is the only party that knows
which screen it was and nothing load-bearing reads it.

**The roster is `search-telemetry.md` §2's `Surface`, unchanged.** Those four are
every place this platform shows one player to another, and a block is offered on
each of them. It is deliberately *not* extended for the expanded card: the card
is reached from a row, so it names the row's surface, and a fifth value would
make the same block record two different things depending on how far the player
had tapped.

**There is no surface on ``PlayerUnblocked``**, and that asymmetry is deliberate.
Unblocking happens in one place — the list of people you have blocked — so a
field naming it would carry no information, and a field with one legal value is a
field somebody eventually widens.
"""

from __future__ import annotations

from enum import Enum


class BlockSurface(str, Enum):
    """The four surfaces of `search-telemetry.md` §2, as a block records them."""

    #: The ranked shortlist — *Find me a game*.
    SHORTLIST = "SHORTLIST"
    #: A seated four the engine composed.
    LINEUP = "LINEUP"
    #: Filling the empty seats of a four the player started.
    FILL_SEATS = "FILL_SEATS"
    #: The one-at-a-time deck — *Match me*.
    DECK = "DECK"
