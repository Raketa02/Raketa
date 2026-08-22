"""What composing Now needs from the rest of the system.

Now is a **read**: it owns no aggregate, writes nothing and stores nothing. What
it owns is the composition — which regions exist, in what order, and what a card
carries — and everything it composes *from* belongs to another context.

That is exactly what makes the ports load-bearing here rather than ceremonial. A
use case reaching into ``MatchRepository`` or ``SkillRatingRepository`` directly
would put another context's vocabulary in the composer's constructor, and the
composer would then have to be changed every time that context reshaped a read it
never asked for. A port states what Now needs in Now's words; the adapter beside
it is the one place that knows whose question it really is.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Sport


@runtime_checkable
class RatedSports(Protocol):
    """Which sports a player holds a rating at.

    The definition of ``all`` on the sport bar, and it is a **rating** rather than
    a declaration on purpose: the sports picker persists nothing, so a rating is
    the only durable record that a player plays a sport at all. A shelf called
    *Best fit for you* filtered by ``all`` is then a claim about her and not about
    inventory.

    Returns a set rather than a list: nothing downstream reads an order out of it,
    and a list would invite one.
    """

    async def for_player(self, player_id: UUID) -> frozenset[Sport]:
        ...
