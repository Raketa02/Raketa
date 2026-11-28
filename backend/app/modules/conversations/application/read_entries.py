"""*The page before this one.*

**One code path serves history and catch-up**, which is the property
``docs/adr/0147`` bought by making the cursor a sequence rather than an offset: a
client that has been away and finds a hole below the newest page walks backward
through this same route until it reaches its own high-water mark.

**No header here**, and no ``read_at``. A page of entries is folded against
nothing — every entry carries its own moment — so an instant beside it would be a
second clock for a client to reconcile against the one the detail read already
gave it.

**No ``has_more``.** The sequence is gapless, so ``seq`` 1 *is* the beginning.

**But a page does carry the faces of whoever it names**
([#408](https://github.com/Rakieta02/Rakieta/issues/408)), and that is not a
header: it is the one thing a client cannot fill from what the detail read gave
it, because the people a page names are not only the members — the actor of a
``SEAT_LEFT`` line was never one, and that line is on whichever page the *no*
landed on. One face read over the page's own authors and actors, and **nothing
about the roster by choice**: the membership is in hand from the gate, but the
detail read already handed the client every member's face, and a page that
repeated them would be a header under another name.

The gate is membership, exactly as it is on every other route here, and a
non-member gets ``conversation_not_found``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.commands import ReadEntriesCommand
from app.modules.conversations.application.faces import faces_in
from app.modules.conversations.domain.entries import Entry, people_named
from app.modules.conversations.domain.ports import MemberFace, MemberFaces


@final
@dataclass(frozen=True, slots=True)
class EntryPage:
    """One page backward, and the faces of everybody on it."""

    #: Oldest first inside the page. Empty when the cursor was the beginning.
    entries: tuple[Entry, ...]
    #: Every author and every actor on the page, resolved once and ordered by
    #: id. **Not the members**, and not a superset of them: a page names only
    #: what is on it.
    people: tuple[MemberFace, ...]


@final
class ReadEntries:
    """One page of one room's stream, ending just before a cursor."""

    def __init__(self, *, rooms: ARoomOfYours, faces: MemberFaces) -> None:
        self._rooms = rooms
        self._faces = faces

    async def execute(self, command: ReadEntriesCommand) -> EntryPage:
        found = await self._rooms.to_read(command.conversation_id, command.reader_id)
        entries = found.conversation.page_back(
            before_seq=command.before_seq, limit=command.limit
        )
        named = people_named(entries)
        return EntryPage(
            entries=entries,
            people=faces_in(named, await self._faces.faces_of(named)),
        )
