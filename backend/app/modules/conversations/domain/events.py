"""The Conversation context's domain events — **four, and only two are entries.**

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: a player as a ``str`` uuid, a code as its value, a
sport as its code.

**The opening is not an entry.** ``ConversationOpened`` is the news that a room
exists, and ``seq`` 1 is whatever happens next
(``the-words.md`` §23.1). Three membership codes share that one rule: an
acceptance, an invitation and a departure each write a line **only when there was
already a room to write it in**, and the first acceptor is a founding member
visible in membership rather than a sentence in the backlog.

**``GameNoted`` is the other event with no line**, and it is the reason a refused
line is not a refused telling. ``GamePlanned`` reaches this room and draws nothing
— everybody having accepted is an arrangement of the seats, so a *Game on* line
would announce a conclusion the record already implies — but it is where the room
learns the game it is about, and where its own end will be derived from
(``docs/adr/0153`` §2). Dropping the delivery because nothing renders would drop
the anchor with it.

**Every entry event carries its ``seq``**, minted on append under the
conversation row's lock (``docs/adr/0147`` §2). It is **not** the stream version
and must never be inferred from one: the opening event holds a version and no
``seq``, so the two part company at row one and stay parted.

**``SystemLineRecorded`` carries the id of the event that caused it**, and that
field is the whole of this context's idempotency. The outbox is at-least-once by
construction, so a subscriber that writes must be able to recognise a redelivery;
a line whose ``source_event_id`` is already folded is recorded a second time by
nothing. It is not a second identity for the line — ``(conversation_id, seq)`` is
that — it is a statement about what the line was told by.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from uuid import UUID


@dataclass(frozen=True)
class ConversationOpened:
    """A room exists, for the people who have agreed to play.

    Opened by the **first acceptance**, and by a mutual-born challenge's own
    event — which *is* the opening and writes no line, because both seats are
    accepted from birth and there was never a moment with one person in the room.

    It carries the challenge and the sport and **no members**: membership is
    derived from whichever record is currently arranging (``docs/adr/0146`` §7),
    and a roster stored here would be the copy that decides who may read the
    messages and the first one to go wrong.
    """

    conversation_id: UUID
    challenge_id: UUID
    sport: str
    occurred_at: datetime


@dataclass(frozen=True)
class GameNoted:
    """The line-up completed, so this room is now about a game.

    **Writes no line.** What a player sees instead is the plan card appearing and
    membership stopping — drawn, not announced.
    """

    conversation_id: UUID
    game_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class MessageSent:
    """One player's own words, at one sequence number."""

    conversation_id: UUID
    seq: int
    author_id: UUID
    client_message_id: UUID
    text: str
    occurred_at: datetime


@dataclass(frozen=True)
class SystemLineRecorded:
    """Something that happened elsewhere, told here as a code and its values."""

    conversation_id: UUID
    seq: int
    code: str
    actor_id: UUID | None
    values: Mapping[str, str]
    #: The outbox row that caused this line. See the module docstring: it is what
    #: makes a redelivery record nothing, and it is never an identity.
    source_event_id: UUID
    occurred_at: datetime

    def __post_init__(self) -> None:
        # The codec decodes a JSON object back as a ``dict``; forcing a plain
        # ``dict`` of ``str`` here is what keeps an event that has been through
        # the store equal to the event that was appended, exactly as the seating
        # events' ``_retuple`` does for their arrays.
        object.__setattr__(
            self, "values", {str(k): str(v) for k, v in dict(self.values).items()}
        )
