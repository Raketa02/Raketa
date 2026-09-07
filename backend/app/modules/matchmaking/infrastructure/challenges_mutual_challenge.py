"""``MutualChallengeMinting``'s adapter — the one call across the arrow.

A translation and nothing more: the matcher's question is *open their game*, and
the other context's command is ``OpenFromMutualInterestCommand``. Keeping the two
sentences apart is what lets ``challenges`` grow another reason to refuse a mint
— or another field on the command — without the matcher's shape changing.

**It reads the provider's own use case and never the provider's aggregate.** The
factory that decides what a mutual-born challenge *is* — both seats accepted, no
deadline, the pair in the court's first two positions — belongs to ``challenges``,
and a ``Challenge.opened_from_mutual_interest`` call written here would make the
matcher a second author of it. This is ``UsersAccountStatus``'s shape, one
direction over.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Sport
from app.modules.challenges.application.commands import (
    OpenFromMutualInterestCommand,
)
from app.modules.challenges.application.open_from_mutual_interest import (
    OpenChallengeFromMutualInterest,
)


@final
class ChallengesMutualChallenge:
    """Opens the game ``challenges`` says these two now have."""

    def __init__(self, opening: OpenChallengeFromMutualInterest) -> None:
        self._opening = opening

    async def open_from_mutual_interest(
        self, *, sport: Sport, player_id: UUID, other_player_id: UUID
    ) -> UUID | None:
        return await self._opening.execute(
            OpenFromMutualInterestCommand(
                sport=sport,
                player_id=player_id,
                other_player_id=other_player_id,
            )
        )
