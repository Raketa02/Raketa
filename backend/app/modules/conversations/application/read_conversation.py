"""*One room: who is in it, and what has just happened.*

**The header and the newest page come back in one fold**, against one instant, so
members and entries can never disagree (``docs/adr/0148`` §3). Two reads would let
a client draw a bubble from somebody the membership it is holding does not
contain.

**The gate is membership and nothing is re-gated against the reader**
(``docs/adr/0143`` §2, applied one surface over). The four fail-closed safety
gates ran over every pair of the court in the send's own transaction; re-running
them here would tell a reader that something changed about somebody else, which is
the one thing a safety gate may never say.

**A non-member gets ``conversation_not_found``**, the same code a room that does
not exist gets. One code for two cases, on ``challenge_not_found``'s argument: a
403 here would answer *is this id real* about a stranger's evening.

**And there is no ``read_at`` on the entries route beside this one**, because that
route carries no header — this is the response whose membership is a fold, and
this is the one that says when it was folded.

**The faces are resolved for everybody the response names, not only for the
roster** ([#408](https://github.com/Rakieta02/Rakieta/issues/408)). Membership is
derived live, so the person a ``SEAT_LEFT`` line is about has by definition just
left it — and the one line whose actor is never a member was the one line a
roster lookup could not name. One face read over the union, and ``people`` is
what it answered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, Sport
from app.modules.conversations.application.commands import ReadConversationCommand
from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.faces import faces_in
from app.modules.conversations.domain.entries import Entry, people_named
from app.modules.conversations.domain.paging import PAGE_LIMIT_DEFAULT
from app.modules.conversations.domain.ports import MemberFace, MemberFaces


@final
@dataclass(frozen=True, slots=True)
class OpenedConversation:
    """A room's header and its newest page, folded together."""

    conversation_id: UUID
    booking_id: UUID
    game_id: UUID | None
    sport: Sport
    members: tuple[MemberFace, ...]
    #: Everybody this response names — the members, and every author and actor
    #: on the page — resolved once, against the same instant. A superset of
    #: ``members``, so a current member is the same face in both.
    people: tuple[MemberFace, ...]
    #: Oldest first inside the page, which is the order a stream is drawn in.
    #: The page's own start is ``entries[0].seq``; there is no ``has_more``
    #: because ``seq`` 1 is the beginning of the conversation.
    entries: tuple[Entry, ...]


@final
class ReadConversation:
    """One room, read by somebody who is in it."""

    def __init__(
        self,
        *,
        rooms: ARoomOfYours,
        faces: MemberFaces,
        clock: Clock,
    ) -> None:
        self._rooms = rooms
        self._faces = faces
        self._clock = clock

    async def execute(
        self, command: ReadConversationCommand
    ) -> tuple[Instant, OpenedConversation]:
        now = self._clock.now()
        found = await self._rooms.to_read(command.conversation_id, command.reader_id)
        room, members = found.conversation, found.members

        entries = room.page_back(before_seq=None, limit=PAGE_LIMIT_DEFAULT)
        named = members | people_named(entries)
        faces = await self._faces.faces_of(named)
        return now, OpenedConversation(
            conversation_id=room.conversation_id,
            booking_id=room.booking_id,
            game_id=room.game_id,
            sport=room.sport,
            members=faces_in(members, faces),
            people=faces_in(named, faces),
            entries=entries,
        )
