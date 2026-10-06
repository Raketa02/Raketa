"""**Who is in a room**: the people on its game's court, right now.

*The people booked on this game* — the game's **current** line-up
(``docs/adr/0146`` §7, as ``docs/adr/0162`` amended it: a seat can be left and
re-seated, and the line-up is read live either way). A room is opened only by a
booked game and is born about it (#575), so the game is the one record a room's
membership is read from.

**Derived, never stored.** A roster on the conversation would make *who is in
this* true in a second place, and the first copy to go wrong is the one deciding
who may read the messages.

**A room moves with its court.** A room whose game lost somebody draws the
three, and the newcomer the moment the re-seat commits.

**One question for a whole list, never one per room.** *Question* rather than
*query*: a game is an event stream, so a provider may fold one aggregate per id
behind the call — what this fold promises is that it does not loop, not that
the store does not.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Mapping
from uuid import UUID

from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.ports import PlayedCourt


class Membership:
    """Who is in these rooms, right now."""

    def __init__(self, *, played: PlayedCourt) -> None:
        self._played = played

    async def of(self, rooms: Sequence[Conversation]) -> Mapping[UUID, frozenset[UUID]]:
        """Each room's members, keyed by conversation id.

        A room whose game answers about nobody — or that has no game — is
        **absent from the answer** rather than present with an empty court. An
        empty membership would let anybody read it, which is the one way this
        fold is allowed to fail.
        """

        by_game = {
            room.game_id: room.conversation_id
            for room in rooms
            if room.game_id is not None
        }
        line_ups = await self._played.line_ups_of(tuple(by_game))
        return {
            conversation_id: found
            for game_id, conversation_id in by_game.items()
            if (found := line_ups.get(game_id))
        }

    async def of_one(self, room: Conversation) -> frozenset[UUID]:
        """One room's members. Empty when its game answers about nobody."""

        found = await self.of((room,))
        return found.get(room.conversation_id, frozenset())
