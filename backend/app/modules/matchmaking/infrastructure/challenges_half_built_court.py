"""``HalfBuiltCourtQuery``'s adapter — the court a fill names, translated.

``challenges`` may not import the matcher, so this class sits on the matcher's
side of the arrow and reads the provider's own port, exactly as
``ChallengesButNobodyHasPlayed`` does for the history. What crosses is
``challenges``' vocabulary; this is where the two spellings meet.

**It reads the provider's port and never the provider's streams.** The fold over
a challenge log belongs to ``challenges``; a ``select`` over the event store
written here would make the matcher a second reader of somebody else's log and a
second author of what *still being arranged* means.

**The clock is read here rather than demanded of the caller**, which is the same
decision ``open_challenges`` takes one class over: whether a court is still being
arranged is a fact about this instant, and a caller that could supply the instant
could supply a stale one.

**One provider, one contract.** Unlike ``MatchHistoryQuery`` there is no seam
running through this read: every fact on it is a challenge fact, so nothing
composes with it and nothing will.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Clock, instant
from app.modules.challenges.domain.ports import ChallengeHistoryQuery
from app.modules.matchmaking.domain.ports import HalfBuiltCourt


@final
class ChallengesHalfBuiltCourts:
    """Answers the matcher about one challenge the filler is on."""

    def __init__(self, challenges: ChallengeHistoryQuery, clock: Clock) -> None:
        self._challenges = challenges
        self._clock = clock

    async def half_built_court(
        self, *, challenge_id: UUID, member_id: UUID
    ) -> HalfBuiltCourt | None:
        """That court, in the reader's vocabulary, or nothing.

        **A field-for-field translation and deliberately nothing more.** The
        provider decides who is seated, who has gone and whether the court is
        still being arranged; a rule applied here would be a second opinion about
        a challenge, held by the context that does not own one.
        """

        found = await self._challenges.half_built_line_up(
            challenge_id=challenge_id,
            member_id=member_id,
            now=instant(self._clock.now()),
        )
        if found is None:
            return None
        return HalfBuiltCourt(
            challenge_id=found.challenge_id,
            sport=found.sport,
            mode=found.mode,
            seated_ids=found.seated_ids,
            answered_and_gone=found.answered_and_gone,
        )


__all__ = ["ChallengesHalfBuiltCourts"]
