"""What a caller asks this context to do. Two commands, and neither has a reason.

Both name the blocker explicitly rather than taking it from an ambient
*current user*: a use case that read the caller from somewhere would be a use
case a seed run or a management command could not drive, and the boundary is
where an identity comes from a token.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BlockPlayerCommand:
    """*Keep this person off my court.*

    **The pair and nothing else.** There is no reason field — a reason belongs
    to a Report, and this command is the shape that would otherwise be the
    obvious place to add one — and no screen (``docs/adr/0193`` §5).
    """

    blocker_id: UUID
    blocked_id: UUID


@dataclass(frozen=True, slots=True)
class UnblockPlayerCommand:
    """Lift **my own** block of this person. The other direction is untouched."""

    blocker_id: UUID
    blocked_id: UUID
