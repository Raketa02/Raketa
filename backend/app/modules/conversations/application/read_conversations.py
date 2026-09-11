"""*Which rooms am I in, and what happened last in each.*

One read, keyed on the reader and on nothing else — the shape every read in this
repository that could otherwise ask about a stranger's evening takes.

**No pill, and no standing anywhere on a row** (``docs/adr/0148`` §6). Reading one
would make the conversation ask ``challenges`` and ``games`` what they are, which
is the one thing it never does — and it does not need to ask, because it has
already been told: **the last entry is what a pill would have said**, and a pill
beside it would be the second place one fact is true.

**Ordered by the last entry, newest first.** A chat list rises on activity. A room
where nothing has happened yet has no last entry at all — the opening is not a
line (``the-words.md`` §23.1) — so it orders on the moment it opened, which is the
only instant it has.

**The list earns a ``read_at`` because its very membership is a fold**
(``docs/adr/0148`` §10): a room is destroyed rather than delisted, so whether a row
appears at all was decided against an instant.

**A room past its end is dropped here and not by the sweep** (``docs/adr/0153``
§5). The end is derived and the sweep exists to make the destruction real rather
than to make the answer right, so the list drops a room the moment it is over —
and a run of the sweep changes which rows the store returns and never which rows
this answers with.

**Three set reads for a whole list.** The rooms, then membership over two records,
then the faces of everybody in any of them **and everybody a last entry names**.
Never one question per room.

**A row names its people, and they are not only its members**
([#408](https://github.com/Raketa02/Raketa/issues/408)). The person a
``SEAT_LEFT`` line is about has by definition just left the membership, and the
row's second line is that entry more often than any other — so ``people`` is
everybody the row names, resolved in the same read as the roster, and the
roster stays the roster.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, final
from uuid import UUID

from app.kernel import Clock, Instant, Sport
from app.modules.conversations.application.commands import ReadConversationsCommand
from app.modules.conversations.application.faces import faces_in
from app.modules.conversations.application.membership import Membership
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import Entry, Message, people_named
from app.modules.conversations.domain.lifetime import has_ended
from app.modules.conversations.domain.ports import (
    ArrangingCourt,
    ConversationDirectory,
    MemberFace,
    MemberFaces,
)


@final
@dataclass(frozen=True, slots=True)
class ConversationRow:
    """One room, as a row in the Chats tab.

    **The members are the room's and never the court's.** A doubles line-up that
    is still filling draws the two people who have accepted, because a row that
    drew four faces for a two-member room would be drawing the court.

    ``last_entry`` is ``None`` in a room whose first acceptance is its whole
    history. That is a real state rather than an edge case, and it is why the
    field is nullable: the opening writes no line.

    ``game_id`` is nullable because a ``LINE_UP_INCOMPLETE`` room has no game —
    which is what a client draws its *Details* door from, and why the door is
    absent rather than disabled.
    """

    conversation_id: UUID
    challenge_id: UUID
    game_id: UUID | None
    sport: Sport
    members: tuple[MemberFace, ...]
    #: Everybody this row names — the members, and whoever ``last_entry`` is
    #: about — each resolved once. A superset of ``members``, never a
    #: replacement for it: the roster is a fact about the court, and this is a
    #: fact about the drawing.
    people: tuple[MemberFace, ...]
    last_entry: Entry | None
    #: The instant this room last moved, and what the list is ordered on. It is
    #: not on the wire: a row carries its last entry, and the entry carries its
    #: own moment.
    moved_at: Instant


@final
class ReadConversations:
    """Every room this player is a member of, the ones that moved last first."""

    def __init__(
        self,
        *,
        directory: ConversationDirectory,
        arranging: ArrangingCourt,
        membership: Membership,
        faces: MemberFaces,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._arranging = arranging
        self._membership = membership
        self._faces = faces
        self._clock = clock

    async def execute(
        self, command: ReadConversationsCommand
    ) -> tuple[Instant, tuple[ConversationRow, ...]]:
        now = self._clock.now()

        # **Found through the challenges this player accepted**, which reaches
        # every room including the ones whose line-up has completed: a game's
        # line-up is frozen from those very seats and nothing in ``games`` can
        # move anybody. Which record membership is then *read from* is still the
        # two-record rule below.
        rooms = await self._directory.for_challenges(
            await self._arranging.accepted_by(command.reader_id)
        )
        # **Dropped before membership is asked**, exactly as ``ARoomOfYours``
        # drops one: the end is a fold over the room's own stream and is already
        # in hand, while membership is two reads into other contexts — and a room
        # that is over is one nobody needs them for.
        standing = tuple(room for room in rooms if not has_ended(room, now=now))
        members = await self._membership.of(standing)

        mine = tuple(
            room
            for room in standing
            if command.reader_id in members.get(room.conversation_id, frozenset())
        )
        named = {
            room.conversation_id: _named_by(room, members[room.conversation_id])
            for room in mine
        }
        faces = await self._faces.faces_of(
            {player_id for room in mine for player_id in named[room.conversation_id]}
        )

        rows = tuple(
            _row(
                room,
                members[room.conversation_id],
                named[room.conversation_id],
                faces,
            )
            for room in mine
        )
        return now, tuple(sorted(rows, key=lambda row: row.moved_at, reverse=True))


def _named_by(room: Conversation, members: frozenset[UUID]) -> frozenset[UUID]:
    """Everybody the row names: the roster, and whoever the last entry is about."""

    last = room.last_entry
    return members | people_named(() if last is None else (last,))


def _row(
    room: Conversation,
    members: frozenset[UUID],
    named: frozenset[UUID],
    faces: Mapping[UUID, MemberFace],
) -> ConversationRow:
    last = room.last_entry
    return ConversationRow(
        conversation_id=room.conversation_id,
        challenge_id=room.challenge_id,
        game_id=room.game_id,
        sport=room.sport,
        members=faces_in(members, faces),
        people=faces_in(named, faces),
        last_entry=last,
        # A room where nothing has happened yet orders on the moment it opened,
        # which is the only instant it has. Falling back to the epoch would sink
        # a brand-new room to the bottom of the list it was just added to.
        moved_at=_moment_of(last) if last is not None else room.opened_at,
    )


def _moment_of(entry: Entry) -> Instant:
    """When this entry landed.

    The two shapes spell it differently on purpose — a message was **sent** and a
    line **occurred** — so this is the one place the difference is flattened, and
    it is flattened for ordering rather than for the wire.
    """

    return entry.sent_at if isinstance(entry, Message) else entry.occurred_at
