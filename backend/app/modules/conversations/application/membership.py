"""**One rule read against two records**, and this is the file it lives in.

*The people who have agreed to be on this court right now* — the challenge's
accepted seats until the line-up completes, the game's frozen line-up after
(``docs/adr/0146`` §7). It is one rule rather than two, and what selects the
record is the room's own nullable ``game_id``: a room that has been told its
line-up completed reads the game, and every other room reads the challenge.

**Derived, never stored.** A roster on the conversation would make *who is in
this* true in a second place, and the first copy to go wrong is the one deciding
who may read the messages.

**It grows one acceptance at a time and then stops.** A doubles room whose
line-up is still filling draws the members it has, because a row that drew four
faces for a two-member room would be drawing the court rather than the room.

**Two questions for a whole list, never one per room.** The rooms are split by
which record answers about them and each side is asked once. *Questions* rather
than *queries*: both records are event streams, so a provider may fold one
aggregate per id behind either call — what this fold promises is that it does not
loop, not that the store does not.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Mapping
from uuid import UUID

from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.ports import ArrangingCourt, PlayedCourt


class Membership:
    """Who is in these rooms, right now."""

    def __init__(self, *, arranging: ArrangingCourt, played: PlayedCourt) -> None:
        self._arranging = arranging
        self._played = played

    async def of(self, rooms: Sequence[Conversation]) -> Mapping[UUID, frozenset[UUID]]:
        """Each room's members, keyed by conversation id.

        A room whose record answers about nothing is **absent from the answer**
        rather than present with an empty court. An empty membership would let
        anybody read it, which is the one way this fold is allowed to fail.
        """

        by_game = {
            room.game_id: room.conversation_id
            for room in rooms
            if room.game_id is not None
        }
        by_challenge = {
            room.challenge_id: room.conversation_id
            for room in rooms
            if room.game_id is None
        }

        line_ups = await self._played.line_ups_of(tuple(by_game))
        courts = await self._arranging.accepted_on(tuple(by_challenge))

        members: dict[UUID, frozenset[UUID]] = {}
        for game_id, conversation_id in by_game.items():
            found = line_ups.get(game_id)
            if found:
                members[conversation_id] = found
        for challenge_id, conversation_id in by_challenge.items():
            found = courts.get(challenge_id)
            if found:
                members[conversation_id] = found
        return members

    async def of_one(self, room: Conversation) -> frozenset[UUID]:
        """One room's members. Empty when the record it names answers about none."""

        found = await self.of((room,))
        return found.get(room.conversation_id, frozenset())
