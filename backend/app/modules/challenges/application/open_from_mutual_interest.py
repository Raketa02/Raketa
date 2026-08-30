"""A challenge born of two yeses that met. **Inline, and it mints nothing when
it cannot.**

*Let's play* is one tap costing nothing, and when the second one lands the two
people have an open game together. The product says so immediately rather than
through a poller: *that player has left the deck for good, because you now have
an open game together* is a promise about what somebody will never see again, and
a promise like that should not depend on a worker running.

**It runs the same check the send runs**, and this is the ticket's finding rather
than a symmetry for its own sake. ``resolve_origin`` has **no freshness bound** —
a search record is immutable and never expires, and the store will happily find
any search of yours, ever — so a *Let's play* can cite a month-old deck deal. Two
month-old yeses with a block taken since would otherwise walk a challenge past
every gate in the product, minted inline, with nobody looking.

**Its whole observable is that no challenge exists afterwards.** There is no
organiser standing at a screen and no press to refuse, so a refusal here has
nowhere to go and nothing to say: the yes stands, the mutual is still a mutual,
and the game simply is not opened. That is also why this returns ``None`` rather
than raising — a raise would roll back the yes, which was somebody's own act and
is not the thing being refused.

**It does not commit.** The mint and the yes that caused it are one transaction
(``docs/adr/0003``'s outbox is deliberately not used here), so the transaction
boundary stays a decision about the *command* and the caller owns it.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Clock, instant
from app.modules.challenges.application.commands import (
    OpenFromMutualInterestCommand,
)
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import TheGatesCouldNotBeEvaluated
from app.modules.challenges.domain.ports import (
    ChallengeRepository,
    OpenChallengeQuery,
)
from app.shared.ids import new_uuid


@final
class OpenChallengeFromMutualInterest:
    """Two yeses, one challenge — or nothing at all, silently."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        open_challenges: OpenChallengeQuery,
        safety: CourtSafety,
        clock: Clock,
    ) -> None:
        self._challenges = challenges
        self._open_challenges = open_challenges
        self._safety = safety
        self._clock = clock

    async def execute(self, command: OpenFromMutualInterestCommand) -> UUID | None:
        """The challenge's id, or ``None`` when nothing was minted."""

        at = instant(self._clock.now())
        pair = frozenset({command.player_id, command.other_player_id})
        try:
            admitted = await self._safety.admits(pair)
        except TheGatesCouldNotBeEvaluated:
            return None
        if not admitted:
            return None
        if await self._open_challenges.open_pairs_among(pair, now=at):
            # Already arranging something, in this sport or any other. A second
            # challenge would be the same two people asked the same question
            # twice, and the first one is the one they answered.
            return None

        challenge = Challenge.opened_from_mutual_interest(
            challenge_id=new_uuid(),
            sport=command.sport,
            organiser_id=command.player_id,
            other_player_id=command.other_player_id,
            occurred_at=at,
        )
        await self._challenges.save(challenge)
        return challenge.id
