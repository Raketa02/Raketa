"""``HiddenMembers`` over the Blocks context's one read, ``BlockQuery``.

**Every surface that shows one player to another consults that port**
(``docs/adr/0095`` §7), and a group's Members list is one of them
(``docs/adr/0183`` §10). ``exclusions_for`` is already the shape this needs —
one flat set, both directions, nothing that could say which way round — so this
adapter only renames it into the Groups context's words.

**It fails closed by letting the provider's refusal through.** ``BlockQuery``
raises ``BlockStateUnavailable`` rather than answer an empty set it cannot stand
behind, and a ``503`` naming the block state is the honest answer for a list that
could not be checked; catching it here could only turn it into something less
true.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.blocks.domain.ports import BlockQuery


@final
class BlocksHiddenMembers:
    def __init__(self, blocks: BlockQuery) -> None:
        self._blocks = blocks

    async def hidden_from(self, reader_id: UUID) -> frozenset[UUID]:
        return await self._blocks.exclusions_for(reader_id)
