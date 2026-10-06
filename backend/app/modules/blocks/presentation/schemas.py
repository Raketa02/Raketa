"""Wire schemas for the Blocks context: one request, and one read of your own.

**A response may carry the reader's own blocks, never anyone's block of the
reader** (``docs/adr/0193`` §3). ``BlockedPlayersResponse`` is one of the two
places a block crosses the wire — the record's ``blocked_by_you`` is the other —
and ``tests/unit/test_no_response_carries_a_block.py`` names both and refuses a
third.

**The blocker is never in a body.** It is the authenticated caller, always, and
a field for it would be a field a request could get wrong — or lie about. What a
block sends is the other party and nothing else: no reason, which belongs to a
Report, and no screen (``docs/adr/0193`` §5).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.blocks.application.blocked_players import BlockedPlayer

#: The default that spells **omitted** — absent from the JSON, never ``null``.
OMITTED: Any = None


class BlockPlayerRequest(BaseModel):
    """*Keep this person off my court.*

    **The other player and nothing else.** There is no reason field and there
    never will be — a reason for a block belongs to a Report, and a request shape
    is where one would be added first — and no screen it was made from.
    """

    player_id: UUID = Field(
        description=(
            "The player to block. The blocker is the authenticated caller and is "
            "never sent."
        ),
    )


class BlockedPlayerSchema(BaseModel):
    """One person you blocked — a name, a photograph, and when."""

    player_id: UUID = Field(
        description="Who you blocked. `DELETE /blocks/{player_id}` unblocks them."
    )
    name: str = Field(
        description="The whole Name, never the nickname."
    )
    photo_id: UUID = Field(
        OMITTED,
        description=(
            "Their current photograph. Omitted when they have none, and omitted "
            "together with `photo_url` — draw their initials."
        ),
    )
    photo_url: str = Field(
        OMITTED,
        description=(
            "A short-lived signed link to that photograph, minted for **this "
            "response**."
        ),
    )
    blocked_at: datetime = Field(
        description=(
            "When you blocked them. Blocking somebody already blocked does not "
            "move it; unblocking and blocking again does."
        )
    )

    @classmethod
    def of(cls, blocked: BlockedPlayer) -> "BlockedPlayerSchema":
        fields: dict[str, Any] = {
            "player_id": blocked.player_id,
            "name": blocked.name,
            "blocked_at": blocked.blocked_at,
        }
        if blocked.photo_id is not None and blocked.photo_url is not None:
            fields["photo_id"] = blocked.photo_id
            fields["photo_url"] = blocked.photo_url
        return cls.model_validate(fields)


class BlockedPlayersResponse(BaseModel):
    """*Blocked players* — everybody **you** blocked, and nobody else's blocks."""

    players: list[BlockedPlayerSchema] = Field(
        description=(
            "Your standing blocks, **newest first**. Empty when you have blocked "
            "nobody — draw *You haven't blocked anyone.* A block you lifted is "
            "not here, and a block of an id nobody holds is not either."
        )
    )

    @classmethod
    def of(cls, listed: tuple[BlockedPlayer, ...]) -> "BlockedPlayersResponse":
        return cls(players=[BlockedPlayerSchema.of(one) for one in listed])
