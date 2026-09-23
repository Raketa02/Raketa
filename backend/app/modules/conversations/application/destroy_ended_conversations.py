"""The sweep — **destroyed, not delisted** (``docs/adr/0142``, ``docs/adr/0153``).

**Correctness does not depend on this loop running.** A room's end is derived
from its own stream, and every route on it already answers
``conversation_not_found`` past that instant whether or not anything has swept
it. What the loop buys is that the destruction is **real**: the entries stop
existing rather than stopping being answered with, which is the difference
between a room that is over and a record with no end. It is the same split
``challenges``' ``lapse`` states about its own sweep and ``entry_closes_at``
states in its docstring.

**It reads candidates and never conclusions.** The directory answers *every room
that still stands*, because a store that could answer *which rooms have ended*
would be the stored ``ends_at`` ``docs/adr/0153`` §5 refuses — the end is only
ever derived, so the derivation is where the decision is taken. It is taken
through ``Lifetime``, the seam every read decides it through: a room with a
game is over on the game's clock, folded off its own stream, and a room without
one is over when its challenge is (``docs/adr/0164`` §6), asked of ``challenges``
— so what this destroys is exactly what the list has already dropped. What keeps
the walk affordable is the thing being swept: a conversation is destroyed rather
than kept, so the table is the size of what is live.

**Idempotent and safe beside itself with no lock** (``docs/adr/0092``): deleting
a room twice deletes it once, and two processes racing over the same walk leave
what one leaves. With N API processes it runs N times per interval, at unrelated
moments, which for a delete keyed on a fold is exactly nothing.

**It holds no cursor.** A half-finished run is re-derived in full by the next
tick, because the walk is the whole table and the decision is a fold — there is
no position to lose.

**What it counts is what a reader would otherwise have to guess.** *The loop is
off* and *the loop is running and nothing has ended* have one symptom — rooms
accumulating — and only one of them is somebody's problem, so the walk is
reported beside the destruction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.conversations.application.lifetime import Lifetime
from app.modules.conversations.domain.ports import (
    ConversationDirectory,
    ConversationRepository,
)


@final
@dataclass(frozen=True, slots=True)
class SweptRooms:
    """What one pass cost and what it did.

    ``walked`` is every room the store still held; ``destroyed`` is how many of
    them were over. A pass that walked many and destroyed none is a healthy
    platform; a pass that walked none is either a quiet database or a broken
    read, and only the two numbers together tell them apart.
    """

    walked: int
    destroyed: int


@final
class DestroyEndedConversations:
    """One sweep of the conversation table. **The whole of the destruction.**"""

    def __init__(
        self,
        *,
        directory: ConversationDirectory,
        conversations: ConversationRepository,
        lifetime: Lifetime,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._conversations = conversations
        self._lifetime = lifetime
        self._uow = unit_of_work
        self._clock = clock

    async def execute(self) -> SweptRooms:
        """Walk every room, destroy the ones whose episode is over, commit once.

        **One instant for the whole pass**, read before the walk: two rooms whose
        ends fall either side of a clock read during the walk would be swept on
        different days for no reason a reader could name.

        **One commit at the end and never one per room.** Nothing here is
        recoverable half way — a run that dies is re-derived in full by the next
        tick — so a transaction per delete would buy nothing and cost a round
        trip each.
        """

        now = self._clock.now()
        rooms = await self._directory.every_room()
        ended = await self._lifetime.ended_among(rooms, now=now)
        for room in rooms:
            if room.conversation_id in ended:
                await self._conversations.destroy(room.conversation_id)
        await self._uow.commit()
        return SweptRooms(walked=len(rooms), destroyed=len(ended))
