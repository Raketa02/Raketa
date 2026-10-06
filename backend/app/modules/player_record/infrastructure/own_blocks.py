"""``BlocksByTheReader`` over the Blocks context's one directed read.

``BlockQuery.blocks_made_by`` answers with the blocks a player **made**, and this
asks it with the reader as the blocker and nobody else — so the answer is about
the reader's own block and cannot be about anybody's block of the reader
(``docs/adr/0193`` §3). A translation into this context's words, and nothing
decided here.

**One read bounded by how many people the reader blocked** — tens of rows, the
same read *Blocked players* takes. **The store failing stands down to ``None``**,
never to ``False``: a block state nobody can read takes no record down
(``docs/adr/0193``, Consequences), and the sheet omits the fact rather than
drawing a guess. Only ``BlockStateUnavailable`` is caught — the port's own word
for *could not be read* — so a bug still fails loudly.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.blocks.domain.ports import BlockQuery


@final
class OwnBlocksOfTheReader:
    def __init__(self, blocks: BlockQuery) -> None:
        self._blocks = blocks

    async def has_blocked(self, *, reader_id: UUID, subject_id: UUID) -> bool | None:
        try:
            own = await self._blocks.blocks_made_by(reader_id)
        except BlockStateUnavailable:
            return None
        return any(block.blocked_id == subject_id for block in own)


__all__ = ["OwnBlocksOfTheReader"]
