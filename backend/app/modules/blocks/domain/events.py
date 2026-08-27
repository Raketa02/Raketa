"""The Blocks context's durable events — two, and what each carries.

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: the two players as their uuids, the surface as its
machine code. Nothing here holds a value object and nothing here holds display
text.

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

**Neither event is a notification.** They ride the outbox because every event in
this codebase does, and the only handler subscribed to them writes an audit line
with no payload in it. Delivering one to the blocked party would break
ADR-0095 §8, which is the promise that makes the control usable at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PlayerBlocked:
    """One player decided they do not want to be shown another, ever again.

    ``surface`` is where they were standing when they decided
    (``surface.py``) — context beside the fact, and never something a rule reads.
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
