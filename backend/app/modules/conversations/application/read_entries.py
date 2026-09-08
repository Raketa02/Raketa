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

The gate is membership, exactly as it is on every other route here, and a
non-member gets ``conversation_not_found``.
"""

from __future__ import annotations

from typing import final

from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.commands import ReadEntriesCommand
from app.modules.conversations.domain.entries import Entry


@final
class ReadEntries:
    """One page of one room's stream, ending just before a cursor."""

    def __init__(self, *, rooms: ARoomOfYours) -> None:
        self._rooms = rooms

    async def execute(self, command: ReadEntriesCommand) -> tuple[Entry, ...]:
        found = await self._rooms.to_read(command.conversation_id, command.reader_id)
        return found.conversation.page_back(
            before_seq=command.before_seq, limit=command.limit
        )
