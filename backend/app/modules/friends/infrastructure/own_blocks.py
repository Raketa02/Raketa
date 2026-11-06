"""``ReadersBlocks`` over the one directed read ``BlockQuery`` has — blocks
**made by** the reader, never of them (``docs/adr/0193`` §3). It fails closed as
that port does: an unreadable block state raises ``BlockStateUnavailable``
rather than answering *you blocked nobody*, which would show the reader a
request their own block hides."""

from __future__ import annotations

from uuid import UUID

from app.modules.blocks.domain.ports import BlockQuery


class OwnBlocks:
    def __init__(self, blocks: BlockQuery) -> None:
        self._blocks = blocks

    async def blocked_by(self, reader: UUID) -> frozenset[UUID]:
        return frozenset(
            block.blocked_id for block in await self._blocks.blocks_made_by(reader)
        )
