"""Wire schemas for the Blocks context. **One request type, and no response type.**

There is no ``BlockResponse`` and there is no list endpoint, and both absences
are the design rather than a stage of it. A block is unrepresentable in a
response (``docs/adr/0095`` §8): nothing this API returns may carry one, so the
only shapes here are the two things a player *sends*.

**The blocker is never in the body.** It is the authenticated caller, always, and
a field for it would be a field a request could get wrong — or lie about. What
crosses the wire is the other party and, for a block, the screen it was made
from.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.blocks.domain.surface import BlockSurface


class BlockPlayerRequest(BaseModel):
    """*Do not show me this person again.*

    ``surface`` is a closed set the client already holds — the four screens that
    show one player to another — and it is validated here rather than by the
    domain because there is no served vocabulary for a client to hold a stale
    version of. Nothing branches on it.

    **There is no reason field and there never will be.** A reason for a block
    belongs to a Report, and a request shape is where one would be added first.
    """

    player_id: UUID = Field(
        description=(
            "The player to block. The blocker is the authenticated caller and is "
            "never sent."
        ),
    )
    surface: BlockSurface = Field(
        description=(
            "Which screen the block was made from. Recorded as context; no rule "
            "reads it."
        ),
    )
