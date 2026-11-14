"""``BlocksEitherWay`` over the one place a block is read, ``BlockQuery`` —
its ``exclusions_for``, both directions as one flat set, so a people row can't
tell which way round a block was made (``docs/adr/0204`` §2, §10). It fails
closed as that port does: ``BlockStateUnavailable``, never an empty set."""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.blocks.domain.ports import BlockQuery


@final
class QueriedBlocksEitherWay:
    def __init__(self, blocks: BlockQuery) -> None:
        self._blocks = blocks

    async def either_way(self, reader: UUID) -> frozenset[UUID]:
        return await self._blocks.exclusions_for(reader)
