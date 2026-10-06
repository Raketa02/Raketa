"""The Conversation context's domain events — **four, and only two are entries.**

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: a player as a ``str`` uuid, a code as its value, a
sport as its code.

**The opening is not an entry.** ``ConversationOpened`` is the news that a room
exists, and ``seq`` 1 is whatever happens next (``the-words.md`` §23.1).

**``GameNoted`` is the other event with no line**, and it is the reason a refused
line is not a refused telling. ``GamePlanned`` reaches this room and draws nothing
— a booked game is announced on Home and its details, not in its own chat — but
it is where the room learns the game it is about, and where its own end will be
derived from (``docs/adr/0153`` §2).

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

**The opening is on its second version** (#575). A room is opened by a booked
game and filed under the **booking**, so the opening names a ``booking_id``; the
first version named the same id ``challenge_id``, from when a challenge's first
acceptance opened rooms too. A stored history outlives the code that wrote it, so
``ConversationOpenedUnderAChallengeId`` still folds — the id it carries is the
booking's for every room a booking opened, and the arrangement's for every other.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from uuid import UUID


@dataclass(frozen=True)
class ConversationOpened:
    """A room exists, for the people booked on one game. **Version 2.**

    Opened by the booked game's own ``GamePlanned``, and filed under the
    booking the game was opened from — so a redelivery finds the room it
    already opened and records nothing.

    It carries the booking and the sport and **no members**: membership is the
    game's current line-up (``docs/adr/0146`` §7), and a roster stored here
    would be the copy that decides who may read the messages and the first one
    to go wrong.
    """

    conversation_id: UUID
    booking_id: UUID
    sport: str
    occurred_at: datetime


@dataclass(frozen=True)
class ConversationOpenedUnderAChallengeId:
    """``conversations.opened`` **version 1**, as stored — read, never written.

    The same fact under the name a room's arrangement had when a challenge's
    first acceptance could open one: ``challenge_id`` is the booking's id on a
    room a booked game opened, and folds as the room's ``booking_id``.
    """

    conversation_id: UUID
    challenge_id: UUID
    sport: str
    occurred_at: datetime


@dataclass(frozen=True)
class GameNoted:
    """The room is about this game — its hour, and when it was booked.

    **Writes no line.** A booked game is announced on Home and its details, and
    its room is born knowing it: the opening and this are one save.
    """

    conversation_id: UUID
    game_id: UUID
    occurred_at: datetime
    #: The hour the game is booked for (#541) — what the room's end is measured
    #: from. ``None`` only on a room a challenge opened, which nothing opens any
    #: more (#575).
    starts_at: datetime | None = None


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
