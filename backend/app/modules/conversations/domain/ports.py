"""What this context stores behind, and what it demands of contexts it does not
write.

**Nothing here is published outward.** A conversation is *told* and tells
nothing (``docs/adr/0146``), so it has no consumers — which is why there is no
provider register for it and why every port below is a demand rather than an
offer.

**Three demands, and two of them are somebody else's.** ``PlayedCourt`` is
``games``', ``MemberFaces`` reaches the Player profile and ``users``, and
``AccountHoldQuery`` is a spelling of a port whose provider does not exist yet.
Each is contracted in ``tests/demands/`` over every registered implementation,
because *a demand nobody executes is a demand satisfied by accident*.

**A room is opened only by a booked game, and both its membership and its finding
read the game** (#575). Membership is the game's current line-up; the rooms a
player is in are the rooms filed under the bookings of the games they are on.
There used to be a second record — a challenge's accepted seats, until its
line-up completed — and a second port for it; nothing opens a room that way any
more, so nothing reads it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import invariant
from app.modules.conversations.domain.conversation import Conversation


@runtime_checkable
class ConversationRepository(Protocol):
    """How this context loads and saves its own aggregate.

    **``load_for_append`` is not ``load``**, and the difference is the whole of
    ``docs/adr/0147`` §2: an append reads and writes ``last_seq`` under the
    conversation row's lock, so the read that precedes a write takes that lock
    and the read that precedes a response does not. Two methods rather than a
    flag, because a caller that forgot the flag would mint a duplicate sequence
    number under load and nothing would notice until two people saw one bubble
    twice.

    **Nothing here commits.** The transaction boundary is the use case's — and
    for a telling it is the outbox delivery's, so a system line and the outbox
    row that caused it stand or fall together.
    """

    async def load(self, conversation_id: UUID) -> Conversation | None: ...

    async def load_for_append(self, conversation_id: UUID) -> Conversation | None:
        """The same aggregate, with the row locked for a sequence to be minted."""
        ...

    async def for_booking(self, booking_id: UUID) -> Conversation | None:
        """The room this booking's game already opened, if it has.

        **Locked like ``load_for_append``**, because its caller is the opening
        itself: this is the read that makes *one booking is one room* an
        invariant rather than a race between two deliveries arriving together.
        """
        ...

    async def save(self, conversation: Conversation) -> None: ...

    async def destroy(self, conversation_id: UUID) -> None:
        """Delete the room and its whole stream. **Destroyed, not delisted.**

        ``docs/adr/0142``, with its instant moved by ``docs/adr/0153``. Two
        callers: the call-off, which destroys the room in the same act, and the
        sweep, which makes every other ending real.

        **There is no sequence left to have a gap in**, which is what *destroyed*
        buys over a flag: a deleted room cannot be inferred from a hole in a
        neighbour's numbering, because nothing of it survives to be numbered
        beside.

        **Idempotent**, because both callers can run beside themselves: a room
        that is not there is the state this asks for.
        """
        ...


@runtime_checkable
class ConversationDirectory(Protocol):
    """*Which rooms are these?* The list read's only store question."""

    async def for_bookings(
        self, booking_ids: Collection[UUID]
    ) -> tuple[Conversation, ...]:
        """Every room the store still holds that one of these bookings opened.

        **Still holds, rather than still live**, and the difference is
        ``docs/adr/0153`` §5: a room's end is a fold over its own stream, so it is
        the caller that drops one past its end and the sweep that eventually
        removes the row. A store that could answer *which of these are live*
        would be the stored ``ends_at`` that record refuses.

        **One set read over the whole answer**, never one per booking, which is
        the shape every set read in this codebase takes.

        The order is not part of the demand: the list is ordered by its last
        entry (``docs/adr/0148`` §11), which is a fold and belongs to the use
        case rather than to the store.
        """
        ...

    async def every_room(self) -> tuple[Conversation, ...]:
        """Every room that still stands. **The sweep's only store question.**

        **It narrows on nothing, and it cannot.** A room's end is derived from
        its own stream (``docs/adr/0153`` §5), so there is no column to filter on
        and a store that could answer *which rooms have ended* would be the
        stored ``ends_at`` that record refuses. The sweep folds each one and
        decides.

        What keeps that affordable is the thing being swept: a conversation is
        **destroyed** rather than kept, so this table is the size of what is
        live — the same argument ``docs/adr/0127``'s expiry loop makes about the
        interest ledger, read one context over.

        **Ordered, because a set is never the source of a traversal**
        (``docs/adr/0105`` §1). Nothing downstream can observe it, which is why
        the rule is stated on the traversal rather than on what is visible.
        """
        ...

    async def for_game(self, game_id: UUID) -> Conversation | None:
        """The room about this game, if it has one.

        **Locked like ``load_for_append``**, because its callers are tellings
        that write: the *played* line, and the call-off that destroys the room.
        ``GamePlayed`` names a game and nothing else, so this is the way back to
        the room.
        """
        ...


@runtime_checkable
class PlayedCourt(Protocol):
    """The **game's** current line-up. ``games``'.

    The record membership is read from: a seat can be left and re-seated
    (``docs/adr/0162``), and the roster reads the game live either way.
    """

    async def line_ups_of(
        self, game_ids: Collection[UUID]
    ) -> Mapping[UUID, frozenset[UUID]]:
        """Who is on the court of each of these games. **One question, one call.**

        A game absent from the answer is one this reader may not be told about,
        and its room is dropped rather than drawn empty.
        """
        ...

    async def bookings_played_by(self, player_id: UUID) -> frozenset[UUID]:
        """The booking every game this player is on the court of was opened
        from — the arrangement the game carries, which is what its room is filed
        under (#541, #542).

        **Candidates, not conclusions**: whether the player is a member of each
        room is membership's question, read against the game's current line-up.
        """
        ...


@final
@dataclass(frozen=True, slots=True)
class MemberFace:
    """What one person a room names is called and what they look like.

    **Named for the member and answered for everybody the page names.** The
    person a ``SEAT_LEFT`` line is about is by definition no longer a member, and
    the read still resolves their face beside the roster's
    ([#408](https://github.com/Rakieta02/Rakieta/issues/408)); one shape for both,
    because a client fills ``{nickname}`` from one list.

    **A nickname, a photograph, and nothing else.** No Level, no band, no area, no
    score: a card is what somebody reads to decide about a game that might
    happen, and these people are already booked on one. ``docs/adr/0141`` §1
    fixes what may be borrowed about a person on a record of an evening, and this
    room is one.

    ``nickname`` is whole and never written with an @ (``docs/adr/0199`` §1) —
    a room is where people are said, and a player is said by their handle.
    ``None`` for a player ``users`` can no longer name, and never for one with
    no nickname yet, whom the entry gate holds at the naming step. **The member
    keeps their place** — they are still somebody who agreed to play, and
    dropping them would draw a three-person doubles court.

    ``photo_id`` and ``photo_url`` are present **exactly together**. An id with
    no link beside it is a photograph nothing can draw, and neither means the
    client draws the generated court poster, which needs nothing from the wire.

    **Photographs are affordable here where ``docs/adr/0143`` refused them.**
    That record priced a photo per person against a challenges list that keeps
    ended challenges for ever; a room is destroyed rather than kept, so this list
    is bounded and small. A difference between a record and a room, not a change
    of mind.
    """

    player_id: UUID
    nickname: str | None = None
    photo_id: UUID | None = None
    photo_url: str | None = None

    def __post_init__(self) -> None:
        invariant(
            (self.photo_id is None) == (self.photo_url is None),
            f"a photograph with only half an address: {self!r}",
        )


@runtime_checkable
class MemberFaces(Protocol):
    """What the people in a room are called and what they look like.

    **A second spelling of a name read, and the duplication is the decision** —
    ``games`` has its own, for the reason both say: two contexts needing *what
    do I print on this seat* is not a reason for one to own the other's
    vocabulary. This one carries a face beside the name because a room draws
    one and the game's does not.
    """

    async def faces_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, MemberFace]:
        """Each of these players. **One question about the union, never one per
        seat** — a list of rooms asks once, about everybody in any of them, and
        a read asks once about the roster **and** everybody its entries name.

        *One question* rather than *one query*, and the difference is worth
        stating: the names are a set read, but a photograph is chosen off a
        Player profile and a profile is a **stream folded per person**, so the
        implementation pays a fold each. What the port promises is that no caller
        ever loops — not that the provider does not.

        **A player absent from the answer keeps their place.** A member is
        still somebody who agreed to play, and dropping them would draw a
        three-person doubles court — ``games``' rule verbatim; somebody a line
        names is still the person it is about, and the client draws the unknown
        player's mark for them rather than a line naming nobody.
        """
        ...


@runtime_checkable
class AccountHoldQuery(Protocol):
    """Whether an account is under a live hold. **Asked on writes only.**

    ``docs/adr/0148`` §9: *a hold stops you writing anywhere another player sees
    it, and never stops you reading.* The hold's own argument is about **reach**,
    and a message is reach — but a hold must not erase an arrangement other
    people are already inside, so every read here is ungated and the send is not.

    **The matcher's port, spelled again here**, and deliberately: the provider is
    ``cases``, which does not exist, and the alternative to a second spelling is
    this context importing another to ask a safety question.
    """

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        """Which of these players are under a live hold, right now."""
        ...
