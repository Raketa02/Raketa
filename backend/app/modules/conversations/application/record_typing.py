"""*Somebody is typing in the room.*

**A heartbeat, gated exactly like a send, and it appends nothing**
(``docs/adr/0156``).

**Membership is the gate**, and a non-member gets ``conversation_not_found`` —
the same code a room that does not exist gets, and the same one every other act
on this context answers with. A route that told a stranger their heartbeat had
been accepted would answer *is this id real* about somebody else's evening, one
probe a second.

**A hold refuses it** (``docs/adr/0148`` §9). A hold stops you writing anywhere
another player sees it, and a typing indicator is seen by other players — so this
is on the same side of that line as the send, and on the opposite side from every
read.

**It takes ``to_read`` and not ``to_append``, and the difference is the lock.**
``to_append`` takes the conversation row ``FOR UPDATE`` because that is where a
gapless sequence is minted; nothing here mints one, so taking it would serialise
a heartbeat arriving every three seconds against the sends and system lines that
genuinely need it. Same gate, no lock — which is also the shape of the promise
``docs/adr/0156`` §4 makes: **the room's ``last_seq`` is unchanged after any
number of these.**

**There is no commit, because there is no transaction to close.** The write goes
to the ephemeral store and nowhere near Postgres; the only database work in this
use case is the read that decides whether the caller is allowed to do it.

**And the write fails soft**, so a store that is down costs one second of a
courtesy and never costs the caller a ``204``. The wrapper is the composition
root's (``infrastructure/fail_soft_typing.py``); nothing is caught here.
"""

from __future__ import annotations

from typing import final

from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.commands import RecordTypingCommand
from app.modules.conversations.domain.live import TypingHeartbeat
from app.modules.conversations.domain.ports import AccountHoldQuery
from app.shared.domain.errors import AccountHeld


@final
class RecordTyping:
    """One player's heartbeat, into a room they are in."""

    def __init__(
        self,
        *,
        rooms: ARoomOfYours,
        holds: AccountHoldQuery,
        typing: TypingHeartbeat,
    ) -> None:
        self._rooms = rooms
        self._holds = holds
        self._typing = typing

    async def execute(self, command: RecordTypingCommand) -> None:
        await self._rooms.to_read(command.conversation_id, command.player_id)
        # **After membership, and never before it**, exactly as the send does: a
        # stranger is told there is no such room, because telling them their
        # account is held would be an answer about a room they may not know
        # exists.
        if command.player_id in await self._holds.held_among((command.player_id,)):
            raise AccountHeld("This account is under a live hold.")

        await self._typing.typed(
            conversation_id=command.conversation_id, player_id=command.player_id
        )
