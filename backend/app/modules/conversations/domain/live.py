"""The live channel: **two frames, and one of them is still a nudge.**

``docs/adr/0147`` §3 said *a nudge and nothing else on the wire*, and
``docs/adr/0156`` supersedes that sentence and nothing else in it. What a phone
receives when a room **moves** is still ``{v, conversation_id, last_seq}`` and
never a message body, never a system line and never a plan slot; on receiving one
the client fetches from **its own** high-water mark through the ordinary
authenticated read path. What it now also receives is *somebody is typing*, and
that frame is a different kind of thing — see ``Typing``.

Three things follow from the nudge, and they are the whole reason it is two
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

**And two more beside them, for presence, which is neither of those things**
(``docs/adr/0156``). A heartbeat is written to an ephemeral store and a roster is
read back off it; the frame that reaches a phone is built from the roster and
rides the same stream. Neither touches the bus, neither touches Postgres, and
**neither moves a sequence** — a typing frame is not an entry, so the allocator
``docs/adr/0147`` §2 built has nothing to say about it and is never asked.

**Nothing here knows about Redis, SSE or a token.** The bus is one publisher
implementation and the transport is one route; the envelope and the cursor are
what make both swappable, which is the asymmetry ``docs/adr/0147`` chose the
cheapest transport on.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import AsyncGenerator, Collection, Final, Protocol, final, runtime_checkable
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
    """*Room X has moved, and it is now this long.* **One of the two frames.**

    It was *the whole live contract* until ``docs/adr/0156``, which added a
    second frame beside it and took nothing away from this one: a nudge still
    says that something durable has landed, and it is still the only frame that
    carries a sequence.

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


# ---------------------------------------------------------------------------
# Presence. **A heartbeat, a TTL, and no stopped signal anywhere**
# (``docs/adr/0156``).
# ---------------------------------------------------------------------------

#: How often a client re-posts while somebody is typing.
#:
#: **The client's number, stated by the server**, because the three below are one
#: decision and separating them is how they drift: it is published in the route's
#: own description and it is what ``TYPING_TTL`` is chosen against.
TYPING_CADENCE: Final = timedelta(seconds=3)

#: How long one heartbeat stands before the store drops it.
#:
#: **This is the correctness mechanism, and it is the only one.** There is no
#: *stopped* message anywhere in this design — an app that is killed, a phone that
#: loses signal and a request that is dropped all look identical, and each of them
#: would leave a permanent indicator behind if a *stopped* were what cleared it.
#: The failure mode here is the indicator **vanishing**, which is the harmless
#: one.
#:
#: It **must exceed** ``TYPING_CADENCE``, or a heartbeat expires before its
#: successor arrives and the indicator flickers on a player who has not stopped
#: typing. Five against three leaves most of a cadence of slack for a slow
#: request, which is the margin the pair is chosen for rather than a round number.
#:
#: Domain and not configuration, like every other number here: an environment that
#: could shorten it would be an environment that decides whether the indicator
#: works.
TYPING_TTL: Final = timedelta(seconds=5)

#: How often an open stream asks the store who is typing.
#:
#: **It bounds both latencies, in opposite directions.** It is how late an
#: indicator can appear after the first keystroke, and how late it can linger
#: after the last heartbeat expired — so it must be well under ``TYPING_TTL`` or a
#: cleared indicator outlives the fact by more than the fact lasted.
#:
#: The cost is one read per second per open conversation screen, and it is
#: **named rather than hidden**: it is the first number to revisit if the
#: ephemeral store shows pressure, and it is the reason the roster read is one
#: keyed lookup rather than a scan.
TYPING_CHECK: Final = timedelta(seconds=1)

invariant(
    TYPING_CHECK < TYPING_CADENCE < TYPING_TTL,
    "the typing heartbeat's three numbers are one decision and have come apart",
)


@final
@dataclass(frozen=True, slots=True)
class Typing:
    """*These people are typing in room X, right now.* **The second frame.**

    **It carries no sequence and moves none** (``docs/adr/0156`` §4). A typing
    frame is not an entry: nothing is appended, no lock is taken, and the gapless
    allocator ``docs/adr/0147`` §2 built is never asked for a number. That is the
    single invariant this shape exists to make unbreakable — a ``last_seq`` here
    would be a client's cursor moved by something that is not in the room's
    history.

    **It carries the people and not a name**, exactly as every system line does:
    the client fills names from the membership it is already holding, so a
    corrected name fixes the indicator for free and no display text is ever
    frozen onto the wire.

    **A list, because a group chat has more than one possible typist** — and the
    client draws one indicator either way. Sending the set rather than a count
    keeps *whose* answerable on the client, and sending it as one frame rather
    than one per person keeps a room that goes quiet a single frame rather than a
    fade-out somebody has to reconcile.

    **The order is fixed here and not by the store.** A set iterated by whatever
    Redis returned would put ADR-0105's problem on a wire, so ``of`` sorts, and
    two frames about the same two people are the same bytes.

    **And it is content, unlike a nudge, because there is nothing to defer to.**
    A nudge names no content precisely because an authoritative durable read
    exists to be asked instead; presence has no record anywhere, so deferring
    would mean inventing a read route to serve a fact that expires in five
    seconds and asking a phone to call it once a second.
    """

    conversation_id: UUID
    player_ids: tuple[UUID, ...]
    v: int = LIVE_CHANNEL_VERSION

    @classmethod
    def of(cls, conversation_id: UUID, player_ids: Collection[UUID]) -> "Typing":
        """The frame these typists are, in one order. **The only constructor.**"""

        return cls(
            conversation_id=conversation_id, player_ids=tuple(sorted(set(player_ids)))
        )


@runtime_checkable
class TypingHeartbeat(Protocol):
    """*This player is typing in this room, as of now.* **Written, never a state.**

    One call per heartbeat, and there is deliberately no second method: no
    ``stopped``, no ``clear`` and nothing that takes a flag. A store with an *off*
    switch is a store where the switch can fail to arrive, and every way a client
    can vanish is a way it fails to arrive.

    **It fails soft**, like ``NudgePublisher`` and for a stronger version of the
    same reason: a nudge that is lost costs a room its liveness, and a heartbeat
    that is lost costs one second of an indicator that is a courtesy to begin
    with. Every implementation the composition root hands out is wrapped.

    **Idempotent by construction, which is why there is no rate limit.** Writing
    the same key with the same TTL is the cheapest thing this store does, and the
    TTL is what makes repetition harmless — a limiter here would be a second
    mechanism guarding against a cost nobody has measured.
    """

    async def typed(self, *, conversation_id: UUID, player_id: UUID) -> None: ...


@runtime_checkable
class TypingRoster(Protocol):
    """*Who is typing in this room, right now.* **Whatever has not expired.**

    The answer is a fact about the store's own clock and nothing else: there is no
    *who stopped*, no *since when* and no way to ask about a moment other than
    this one. That is the shape that makes ``TYPING_TTL`` the mechanism rather
    than a number some sweep is supposed to honour.

    **It fails soft too, and that is a deliberate departure from the subscriber
    beside it** (``docs/adr/0156`` §6). A subscription *is* the room's liveness,
    so it fails loud and closes the stream; a roster is a courtesy read on the
    **command** client, which is the one with a two-second deadline — so a store
    that is merely slow would close every healthy stream on the platform once a
    second. An unreadable roster reports nobody typing, which is the same answer
    an empty room gives and the same collapse the matcher's ledgers make for the
    same reason.
    """

    async def who_is_typing(self, conversation_id: UUID) -> frozenset[UUID]: ...
