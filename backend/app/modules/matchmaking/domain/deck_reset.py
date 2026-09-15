"""*Show them again* — the fifth durable ledger in the module, and the smallest.

One tap at the end of a deck, and it clears three things at once for one sport
(``docs/adr/0169`` §5): every pass suppression, the day's dealt memory and the
cool-off. What is recorded is **the moment it was pressed**, and nothing else —
because nothing else is what a reset *is*. The three things it clears are each
read off a durable record the deal already holds — the pass row, the search
row, the game — and each of those reads takes this one moment and applies it
its own way (``deck.py``: :func:`~app.modules.matchmaking.domain.deck.cleared_by_reset`,
:func:`~app.modules.matchmaking.domain.deck.dealt_memory_from`,
:func:`~app.modules.matchmaking.domain.deck.cooling_off`). Nothing is deleted
and no cache is touched: a re-shown card is still a re-show, which is the
falsifier ``docs/adr/0128`` §5 protects.

**Durable, and a row rather than a key.** The two things it clears that outlast
a day are read from rows that do not fail soft, so the reset must not either: a
reset that could be lost on a cache outage would re-hide the people a player
just asked to see, which is the *empty the deck* failure every soft ledger here
is soft in order to avoid — arrived at from the other end. And ``docs/adr/0169``
§5 accepts a cost that only a record can pay: ``PASS_SUPPRESS``'s one
falsifier, *pass rate on re-shown profiles*, now has to exclude re-shows a reset
caused, and which those are is computable only while every reset moment is
still on file.

**Append-only, on the pass record's argument.** A second press is a second row
with its own moment, never an update of the first, because a deal between two
presses was shaped by the first and the falsifier above needs to know that. The
deal reads the **latest** one and nothing reads any other; erasure is the only
thing that will ever remove one (``docs/adr/0104`` §3).

**Event-free, on the four ledgers' argument and by the amendment that made it
five** (``docs/adr/0169``, amendment of 2026-09-15). A small fact with no life
story, and nothing subscribes to one being written: the deal reads the moment on
its next run, and that is the whole of what happens.

**Nothing here can answer a question a route could ask.** One write, one read;
the read answers a moment or ``None``, per player and per sport. There is no
list of resets, no count and no *who has reset*, and there will not be — the
route answers ``204`` because there is no shape a reset crosses the wire in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport


@final
@dataclass(frozen=True, slots=True)
class DeckReset:
    """One press of *Show them again*: whose deck, which sport, and when.

    It carries no *what was cleared*. The three things a reset lifts are each
    derived from the record they live on, read against this moment, so a row
    that listed them would be a copy of three other tables free to disagree with
    each of them.
    """

    player_id: UUID
    sport: Sport
    at: Instant


@runtime_checkable
class DeckResetLedger(Protocol):
    """Every *Show them again*, and the one shape it answers in."""

    async def record(self, reset: DeckReset) -> None:
        """Append one reset. **In the caller's own transaction, never committed here.**

        The transaction boundary is the command's decision, exactly as it is for
        the pass and the interest beside it. Append-only: a second press is a
        second row, on the module docstring's argument.
        """
        ...

    async def latest_at(self, *, player_id: UUID, sport: Sport) -> Instant | None:
        """When this player last pressed it for this sport, or ``None`` — never.

        The deal's whole read. Per sport, because the button is on a deck and a
        deck is one sport: a padel reset says nothing about tennis. ``None`` and
        *never pressed* are the same answer, and the deal reads it as *nothing
        cleared*, which is the state everybody starts in.
        """
        ...
