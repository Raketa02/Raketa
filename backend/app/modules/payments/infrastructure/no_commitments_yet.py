"""What could still be charged to a method, while nothing can be.

No proposal takes a yes yet (#540) and no booking holds a game (#541), so every
player has nothing a removed method would be needed for. The day either exists,
an adapter over it is built in ``build_payment_commitments`` instead, and the
refusal already wired to this answer starts firing.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.payments.domain.ports import Commitments


@final
class NoCommitmentsYet:
    """``PaymentCommitments``, answering nought for everybody."""

    async def of(self, player_id: UUID, *, at: Instant) -> Commitments:
        return Commitments(live_yeses=0, upcoming_games=0)
