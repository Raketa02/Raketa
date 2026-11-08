"""``BlocksEitherWay`` over the blocks' own ``BlockQuery`` — **signed here**, so
the arrow runs ``rankings → blocks`` (#772; ``docs/adr/0203`` §8): everybody a
standing block sits between the reader and, either way round, whose rows are
left out of each other's views.

**The blocks' exclusion set, as it stands**: one flat set with no direction in
it, read live over the event log, and **failing closed** — the query raises
``BlockStateUnavailable`` rather than answer an empty set it could not read,
so a ranking read fails before it shows a blocked pair each other's rows.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.blocks.domain.ports import BlockQuery


@final
class QueriedBlocksEitherWay:
    def __init__(self, blocks: BlockQuery) -> None:
        self._blocks = blocks

    async def blocked_either_way(self, reader: UUID) -> frozenset[UUID]:
        return await self._blocks.exclusions_for(reader)
