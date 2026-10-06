"""*Blocked players* — the caller's own blocks, and nobody else's.

**A response may carry the reader's own blocks, never anyone's block of the
reader** (``docs/adr/0193`` §3). This is one of the two reads that do, and it
asks the one directed question ``BlockQuery`` has — *whom has this player
blocked* — with the reader as the blocker, always. There is no parameter here
that could name anybody else, and no read anywhere that answers *who blocked
me*.

**Newest block first**, each person with their face and when the block was
made: the screen is where somebody undoes a mistake, and the most recent one is
the likeliest.

**A block of an id the platform cannot name is left off.** Blocking an id that
belongs to nobody answers exactly as blocking a person does, so the block route
is no oracle for which ids exist (``block_player.py``), and such a block keeps
nobody off anybody's court. There is no face to draw for it, and a row with no
name would be a row nobody could recognise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.blocks.domain.ports import BlockedFaces, BlockQuery


@final
@dataclass(frozen=True, slots=True)
class BlockedPlayer:
    """One person the reader blocked, as the list draws them."""

    player_id: UUID
    name: str
    photo_id: UUID | None
    photo_url: str | None
    blocked_at: Instant


@final
class ReadBlockedPlayers:
    def __init__(self, *, blocks: BlockQuery, faces: BlockedFaces) -> None:
        self._blocks = blocks
        self._faces = faces

    async def execute(self, reader_id: UUID) -> tuple[BlockedPlayer, ...]:
        """The reader's own standing blocks, newest first. Two reads whatever
        the length of the list: the blocks, and every face in one question."""

        own = await self._blocks.blocks_made_by(reader_id)
        if not own:
            return ()
        faces = await self._faces.faces_of([block.blocked_id for block in own])
        listed: list[BlockedPlayer] = []
        for block in own:
            face = faces.get(block.blocked_id)
            if face is None or face.name is None:
                continue
            listed.append(
                BlockedPlayer(
                    player_id=block.blocked_id,
                    name=face.name,
                    photo_id=face.photo_id,
                    photo_url=face.photo_url,
                    blocked_at=block.blocked_at,
                )
            )
        return tuple(listed)
