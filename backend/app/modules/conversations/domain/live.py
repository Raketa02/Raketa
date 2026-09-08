"""The live channel: **a nudge, and nothing else on the wire.**

``docs/adr/0147`` §3. What a phone receives when a room moves is
``{v, conversation_id, last_seq}`` and never a message body, never a system line
and never a plan slot. On receiving one the client fetches from **its own**
high-water mark through the ordinary authenticated read path.

Three things follow from that, and they are the whole reason this module is two
integers and an id.

**A lost frame self-heals.** If the frame carried the entry, a dropped one would
be a hole the client has to detect by arithmetic and repair. Carrying a nudge,
the **next** nudge repairs it for free — because the client asks from its own
cursor and not from the nudge's number. At-most-once on the bus and at-most-once
on the stream stop being two risks and become one harmless one.

**The rule becomes structural.** *Whether the UI may render something it did not
read from the authoritative path* stops being a rule anybody keeps and becomes a
thing the wire cannot express.

**And the shape no check watches is two integers.** A live frame has no
request/response pair for the drift check to diff behaviourally; the declaration
is generated and covered (``presentation/schemas.py``), and the *emission* is
not. That residual hole is affordable precisely because what it covers is this
small — an envelope that carried entries would widen a shape nothing is watching
every time an entry kind was added.

**Two ports, because they fail in opposite directions.** A publish is a courtesy
paid after the record is safe, so it fails **soft** — the message is committed
whatever Redis is doing. A subscription is the liveness itself, so it fails
**loud**: a server whose subscriber is gone closes the stream, and a chat that is
not live looks not-live rather than looking up to date (``docs/adr/0147`` §8).

**Nothing here knows about Redis, SSE or a token.** The bus is one publisher
implementation and the transport is one route; the envelope and the cursor are
what make both swappable, which is the asymmetry ``docs/adr/0147`` chose the
cheapest transport on.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncGenerator, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import invariant
from app.modules.conversations.domain.conversation import Conversation

#: The envelope's version, **carried from the first frame** (``docs/adr/0147``
#: §7). A shipped client parses this shape until that build is gone from phones,
#: and a version added later is one no installed app knows to look for. It is a
#: constant rather than configuration for the reason every domain number here is:
#: an environment that could pick a wire version is an environment that decides
#: what a phone can read.
LIVE_CHANNEL_VERSION = 1


@final
@dataclass(frozen=True, slots=True)
class Nudge:
    """*Room X has moved, and it is now this long.* The whole live contract.

    ``last_seq`` is the conversation row's own allocator (``docs/adr/0147`` §2),
    so publishing costs no second read: the append that minted it wrote it.

    **It is not a cursor the client may fetch from.** The client asks the read
    path from *its own* high-water mark; this number is news that there is
    something to ask for, and a client that fetched from it would reintroduce
    exactly the hole Decision 3 exists to close.
    """

    conversation_id: UUID
    last_seq: int
    v: int = LIVE_CHANNEL_VERSION

    @classmethod
    def about(cls, room: "Conversation") -> "Nudge":
        """The nudge this room's current state is. **The only constructor used.**

        Three places mint one — the send, the telling, and the frame a stream
        opens with — and all three read the same two fields off the same
        aggregate. Assembling it here rather than at each of them is what keeps
        *what a nudge says about a room* one fact: the day it says anything else,
        there is one line to change and three call sites that cannot disagree.
        """

        return cls(conversation_id=room.conversation_id, last_seq=room.last_seq)

    def __post_init__(self) -> None:
        invariant(
            self.last_seq >= 0,
            f"a room cannot have landed {self.last_seq} entries",
        )


@runtime_checkable
class NudgePublisher(Protocol):
    """*Tell whoever is listening that this room moved.* **After the commit.**

    Every implementation handed out by the composition root fails soft: the
    entry is already durable in Postgres by the time this is called, and a bus
    that is down costs the room its liveness rather than costing anybody their
    message.

    **This is a use case's own post-commit write, not a subscriber, and that is
    the repository's existing shape rather than a new one.** ``domain-events.md``
    says side effects happen after commit *in handlers*; the two writes to the
    ephemeral store that already exist take this shape instead, and say so — the
    suppression a pass writes is *"a cache its use case fills after the commit
    rather than a subscriber"*, and ``run_shortlist_search`` writes exposure
    *after the commit* in the same way. A nudge belongs with them: **nothing
    subscribes to a nudge**, it survives nothing, and routing it through the
    outbox would put the poll interval between a person typing and the other
    phones hearing about it — which is the latency the whole record was written
    to avoid. What the outbox still carries is the **event**; this is the
    announcement that the event's effect is now readable.
    """

    async def nudge(self, nudge: Nudge) -> None: ...


@runtime_checkable
class NudgeSubscriber(Protocol):
    """*Everything published about this room, until I stop asking.*

    **An async generator rather than a context manager**, so that whoever opened
    the subscription closes it by closing the iteration — there is exactly one
    lifetime here and it is the stream's, and a second object to remember to
    close is the one that gets leaked on a connection the client dropped.

    **It may raise, and the raise is the point.** A subscriber that cannot be
    reached ends the stream (``docs/adr/0147`` §8): the read path is
    authoritative and independent, so losing this costs latency only, and a
    connection that stayed open delivering nothing would make a dead chat look
    like a quiet one.
    """

    def follow(self, conversation_id: UUID) -> AsyncGenerator[Nudge, None]: ...
