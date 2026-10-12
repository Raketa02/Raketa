"""``SubjectReliability`` over ``player_score``'s published read. **No arithmetic.**

Every figure that crosses here was taken on the other side: the points, the band
and *New* are ``PlayerScore``'s, and the counts are its ``ReliabilityCounts`` —
copied rather than derived. That is the whole reason this file is a mapping — a
figure recomputed here would be a second place for the number a player reads
about themselves to be true, and the copy is always the one that gets believed.

**A set read, narrowed to one person, and the narrowing is this side's job.**
``PublishedScoreQuery`` answers about a whole collection because a group's
Members list holds every member in one call; a record is one deliberate tap, so
this adapter asks about one id and unwraps the answer. The port it satisfies says
so in its signature, which is what stops the shape of the *provider's* caller
leaking into a sheet that will never batch.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.player_record.domain.record import ReliabilityPanel
from app.modules.player_score.domain.ports import PublishedScoreQuery


@final
class ScoreSubjectReliability:
    """The figure, its band, *New* and the counts, in the record's own words."""

    def __init__(self, scores: PublishedScoreQuery) -> None:
        self._scores = scores

    async def reliability_of(
        self, player_id: UUID, *, now: Instant
    ) -> ReliabilityPanel:
        """What the record says of this one person, folded against ``now``."""

        score = (await self._scores.scores_for([player_id], now=now))[player_id]
        counts = score.counts
        return ReliabilityPanel(
            player_score=score.points,
            band=score.band,
            is_new=score.is_new,
            turned_up=counts.turned_up,
            turned_up_of=counts.turned_up_of,
            late=counts.late,
            kept=counts.kept,
            kept_of=counts.kept_of,
            left_in_dispute=counts.left_in_dispute,
        )


__all__ = ["ScoreSubjectReliability"]
