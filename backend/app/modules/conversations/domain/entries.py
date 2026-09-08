"""What rides the stream: **two shapes, one sequence number, and no sentence.**

``docs/adr/0146`` §4 and ``docs/adr/0148`` §4. A **Message** is content — a player
typed it, it crosses as-is, and it has an author in the ordinary sense. A
**system line** is derived from somebody else's event and crosses as **a code and
its values**, because the backend sends codes and never display text
(``docs/adr/0022``) and nobody typed *Tomek set the day*.

**They are two shapes rather than one with a ``kind``.** One shape forces either
a stored rendered sentence — which freezes copy into history, so rewording a line
cannot reword the backlog — or a text field that is real for one arm and
meaningless for the other, which every reader then has to remember.

**Neither carries an id of its own.** ``(conversation_id, seq)`` already
identifies an entry, and a UUID beside a unique key is a second identity for one
row.

**``values`` never repeats what membership already says.** The line carries
``actor_id`` and the client fills ``{name}`` from the members it is already
holding, so a corrected handle reaches the whole backlog for free. That rule is
what keeps ``values`` down to *the count of seats asked*, *which way somebody
left* and *what a slot was set to* — the three facts membership genuinely cannot
supply.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, final
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.conversations.domain.errors import (
    AMessageMustSaySomething,
    TheMessageIsTooLong,
)

#: The longest message this platform accepts, in characters.
#:
#: **Domain and never configuration** — an environment that could pick this is an
#: environment that decides what people may say to each other. It is a cap on a
#: composer that is one line growing to a limit, not a document field, and its
#: falsifier is the first room where somebody genuinely needs to paste more than
#: this into a chat about where to meet on Tuesday.
MESSAGE_LENGTH_CAP = 1000


@final
class SystemLineCode(str, Enum):
    """The codes a system line may carry. **Seven, and the Plan brought three.**

    ``the-words.md`` §23 holds the sentence each one renders; nothing in this
    module knows any of them, which is the point.

    **A seat leaving is one code with the answer as a value**, not two codes.
    *That seat is open again* is the same news either way
    ([#221](https://github.com/Raketa02/Raketa/issues/221)), and **a lapse is
    still not a decline** — the two facts stay apart in the value rather than in
    a second code, which is ``the-words.md`` §13's rule holding one layer down.

    **The Plan's three are the opposite rule applied to the opposite case.**
    Setting a slot and moving one are **the same fact told twice**
    (``docs/adr/0144``), so there is no value telling them apart and no fourth
    code for a change — where a lapse and a decline do the same thing to a
    line-up and *are* two facts. A reader of a plan line cannot tell whether it
    was the first, and has no reason to.
    """

    SEAT_ACCEPTED = "SEAT_ACCEPTED"
    SEATS_INVITED = "SEATS_INVITED"
    SEAT_LEFT = "SEAT_LEFT"
    GAME_PLAYED = "GAME_PLAYED"
    PLACE_RECORDED = "PLACE_RECORDED"
    DAY_RECORDED = "DAY_RECORDED"
    HOUR_RECORDED = "HOUR_RECORDED"


@final
class SeatDeparture(str, Enum):
    """How a seat came to be open again. The value on ``SEAT_LEFT``.

    Two facts, one code above them. Folding them into one would make *answers
    challenges* unmeasurable one layer up, which is exactly the mistake
    ``SeatLapsed`` was split out of ``SeatDeclined`` to avoid.
    """

    DECLINED = "DECLINED"
    LAPSED = "LAPSED"


#: The key ``SEATS_INVITED`` carries its count under, and ``SEAT_LEFT`` its answer.
#: Spelled once here because the writer and the reader are in different layers.
COUNT = "count"
DEPARTURE = "departure"

#: The key all three plan codes carry their slot's value under. **One key for
#: three codes**, because the code already says which slot it is about and a
#: ``place``/``day``/``hour`` triple would be three keys of which two are always
#: absent — a shape every reader would have to branch on to read one string.
#:
#: It is the one value on this list that is **not** a fact membership could
#: supply, which is the test ``values`` is held to: a room knows who its members
#: are and can fill ``{name}`` from ``actor_id``, and it has no way at all to know
#: what somebody typed into a slot.
VALUE = "value"


@final
@dataclass(frozen=True, slots=True)
class MessageText:
    """What somebody typed, **normalised and refused here rather than at a caller**.

    ``backend/CLAUDE.md``: *validate and normalize inside the value object*. It is
    ``Score``'s shape one context over, and for ``Score``'s reason — this is a
    value a **person composes by hand**, so a bad one is a refusal with a code
    rather than an ``invariant``, and the refusal belongs to the type rather than
    to whichever use case happened to receive it.

    **Refused, never fixed.** An empty message and an over-long one each answer
    with their own code: a silently trimmed message is one the sender believes
    they sent whole, in front of other people.
    """

    value: str

    @classmethod
    def of(cls, said: str) -> "MessageText":
        """Trim the ends, then refuse what is left if there is nothing to say.

        Trimming is normalisation and not a fix: a trailing newline from a
        composer is not something the sender typed, and the cap is measured
        against what will actually be shown.
        """

        trimmed = said.strip()
        if not trimmed:
            raise AMessageMustSaySomething()
        if len(trimmed) > MESSAGE_LENGTH_CAP:
            raise TheMessageIsTooLong()
        return cls(value=trimmed)


@final
@dataclass(frozen=True, slots=True)
class Message:
    """What a player typed."""

    seq: int
    author_id: UUID
    #: The client's own id for this send, doing **two jobs** (``docs/adr/0148``
    #: §5): the idempotency key for a resumed send, and the reconciliation key
    #: an optimistic bubble is replaced on. One value, because they are one fact.
    client_message_id: UUID
    text: MessageText
    sent_at: Instant

    def __post_init__(self) -> None:
        invariant(self.seq >= 1, f"an entry before the beginning: seq {self.seq}")


@final
@dataclass(frozen=True, slots=True)
class SystemLine:
    """What happened, as a code and its values. **Never a sentence.**"""

    seq: int
    code: SystemLineCode
    #: Who did it. Nullable because a line that names no actor is a shape the
    #: contract allows (``docs/adr/0148`` §4), not because any code here omits one.
    actor_id: UUID | None
    values: Mapping[str, str]
    occurred_at: Instant

    def __post_init__(self) -> None:
        invariant(self.seq >= 1, f"an entry before the beginning: seq {self.seq}")


#: One ordered stream, two shapes in it. Not a union with a discriminator field:
#: the discriminator is the type, and it is spelled on the wire in
#: ``presentation/schemas.py`` where a JSON reader needs one.
Entry = Message | SystemLine
