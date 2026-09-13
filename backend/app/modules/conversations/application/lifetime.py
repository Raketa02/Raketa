"""**Which of these rooms are over** — one rule read against two records, the
other way round from membership.

A room with a game ends on the game's clock, which is a fold over the room's own
stream (``domain/lifetime.py``): the entry window closing, or a grace after *we
played*. A room without a game **has ended exactly when its challenge is over**
(``docs/adr/0164`` §6) — ``DECLINED``, ``LAPSED``, ``WITHDRAWN`` — which is a fact
about somebody else's record, asked of the port the room already reads its
membership from and never folded here. What selects the record is the room's
own nullable ``game_id``, exactly as it selects membership's.

**Derived on every read, never stored, and never swept into a fact of its own.**
The sweep asks this and destroys what it names; the list read asks this and
drops what it names; ``ARoomOfYours`` asks this and refuses what it names. One
seam, so the three cannot come to two answers about one room — and so that a
room is over the instant its challenge is, whether or not anything has swept.

**Why it is not in ``Membership``.** *Who is in this* and *is this over* are
two questions, and a room whose challenge is over still has members — the
accepted seats are still accepted; there is nobody left to keep faith with, but
nobody un-agreed. Folding them together would make an empty roster the way a
room ends, which is the one way membership is allowed to fail and must not be
how a lifetime succeeds.

**The port is asked about rooms without a game and about nothing else.** A room
with a game keeps the game's clock untouched, and a call-off — by a withdrawal,
or by the departure that left one player on the court (``docs/adr/0165`` §3) —
destroys its room in the act — so a challenge's ending is never the reason a
room with a game stops, and asking would be a stream fold per room for an
answer nothing reads.

**The cost is a second fold of the same small stream.** A room without a game
has its challenge folded here for *over* and again in ``Membership`` for *who is
in* — two questions on one port, a handful of events each. The alternative was
one method answering both in one shape, which would make membership's answer
carry a standing and the two seams one; two folds is the cheaper mistake.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from app.kernel import Instant
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.lifetime import ended_by_its_game
from app.modules.conversations.domain.ports import ArrangingCourt


class Lifetime:
    """Which rooms are over, right now."""

    def __init__(self, *, arranging: ArrangingCourt) -> None:
        self._arranging = arranging

    async def ended_among(
        self, rooms: Sequence[Conversation], *, now: Instant
    ) -> frozenset[UUID]:
        """The conversation ids of every room here that is over at this instant.

        **One question for the whole list, never one per room**, about the rooms
        whose end is the challenge's; the rest are answered off their own
        stream and cost no read at all.
        """

        ended = {
            room.conversation_id for room in rooms if ended_by_its_game(room, now=now)
        }
        by_challenge = {
            room.challenge_id: room.conversation_id
            for room in rooms
            if room.game_id is None
        }
        if by_challenge:
            over = await self._arranging.over_among(tuple(by_challenge), now=now)
            ended.update(by_challenge[challenge_id] for challenge_id in over)
        return frozenset(ended)

    async def has_ended(self, room: Conversation, *, now: Instant) -> bool:
        """Whether this one room is over at this instant."""

        return room.conversation_id in await self.ended_among((room,), now=now)
