"""The Blocks context's durable events — two, and what each carries.

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: the two players as their uuids. Nothing here holds
a value object and nothing here holds display text.

**Two events, and there will not be a third with a reason on it.** A reason for a
block belongs to a *Report* (``docs/adr/0095`` §2), and reporting is out of
scope; a free-text field added here later would be the fastest way to turn a
safety control into a record of what one player thinks of another. There is no
field to add it to and no schema on the wire that could carry it.

**Both events carry the whole pair**, including the one the stream id already
determines. That is not a duplicate copy of the identity in the way an id on the
event would be: ``block_id`` is a ``uuid5`` and cannot be reversed, so a reader
looking at a row — the exclusion query below, an erasure sweep, an auditor —
would otherwise be holding a stream id that names nobody. Carrying both ids is
what makes *every block this player appears in, on either side* a question the
log itself can answer.

**No screen, and a third class for the rows that named one**
(``docs/adr/0193`` §5). ``blocks.player_blocked`` v1 recorded which of the old
loop's four screens a block was made from, and every one of those screens is
gone. v2 is the pair alone. ``PlayerBlockedNamingAScreen`` is v1, kept so a
stored row still decodes; the Block reads it as the same fact and drops the
surface, nothing writes it, and nothing in the store is rewritten. It is a
third *class*, not a third thing a block can be.

**Neither event is a notification.** They ride the outbox because every event in
this codebase does. Two handlers hear a block: one writes an audit line with no
payload in it, and Proposals takes back the blocker's yeses where the blocked
person is In, through the ordinary withdrawal (``docs/adr/0193`` §4). Nothing
delivers either event to the blocked party (``docs/adr/0193`` §3).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PlayerBlocked:
    """One player decided they will not share a court with another.

    ``blocks.player_blocked`` v2: the pair, and when. **No screen**
    (``docs/adr/0193`` §5).
    """

    blocker_id: UUID
    blocked_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class PlayerBlockedNamingAScreen:
    """``blocks.player_blocked`` v1, **read and never written**.

    The same fact as ``PlayerBlocked``, from before ``docs/adr/0193`` §5: it
    also named which of the old loop's four screens the block was made from.
    The Block folds it exactly as it folds v2 and drops ``surface``, which
    nothing ever branched on.
    """

    blocker_id: UUID
    blocked_id: UUID
    surface: str
    occurred_at: datetime


@dataclass(frozen=True)
class PlayerUnblocked:
    """The same player lifted their own block. **Only their own.**

    The other direction is a different stream and is untouched by this event,
    which is the whole reason the record is directed
    (``docs/adr/0095`` §2).
    """

    blocker_id: UUID
    blocked_id: UUID
    occurred_at: datetime
