"""What a caller asks this context to do.

The organiser is named explicitly rather than taken from an ambient *current
user*, for the reason every command in this codebase is: a use case that read the
caller from somewhere would be a use case a seed run or a management command
could not drive, and the boundary is where an identity comes from a token.

**The arrangement travels whole.** It is the sides the organiser built, in the
court's own order, and it is what the invitee will be answering — never a better
one worked out afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.challenges.domain.seats import SeatPlan
from app.modules.player_profile.domain.availability import Window


@dataclass(frozen=True, slots=True)
class SendChallengeCommand:
    """*Ask everybody on this court to play.*

    ``window`` is derived by the caller from **the grid the search actually ran
    on** and is stamped onto the challenge here. It is not asked for and there is
    no picker anywhere: a player changes their window by changing their grid,
    which is the same act that changes their matches (ADR-0100).

    ``mode`` is ``None`` exactly when the surface the court was built on has no
    mode — the deck deals one card at a time and asks nobody to pick one.
    """

    organiser_id: UUID
    sport: Sport
    mode: SearchMode | None
    window: Window
    arrangement: tuple[SeatPlan, ...]
