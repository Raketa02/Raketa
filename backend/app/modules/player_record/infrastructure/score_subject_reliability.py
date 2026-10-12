"""``SubjectReliability`` over ``player_score``'s published read. **No arithmetic.**

Every figure that crosses here was taken on the other side: ``PlayerScore.published``
is the pill and ``StrandRatio.value`` is each row's, both copied rather than
derived. That is the whole reason this file is three lines of mapping and a walk
— a blend recomputed here would be a second place for the number a player reads
about themselves to be true, and the copy is always the one that gets believed.

**A set read, narrowed to one person, and the narrowing is this side's job.**
``PublishedScoreQuery`` answers about a whole collection because its other caller
holds five hundred candidates in one search; a record is one deliberate tap, so
this adapter asks about one id and unwraps the answer. The port it satisfies says
so in its signature, which is what stops the shape of the *provider's* caller
leaking into a sheet that will never batch.

**Absence passes straight through.** A player the platform has watched nothing of
is missing from the provider's mapping, is ``None`` here, and is a zone the
response omits — one spelling, all the way out, because *no record* becoming *a
bad record* is the one thing this chain exists to prevent.

**The rows walk the vocabulary and never the mapping.** ``ReliabilityStrand``'s
own order is what a reader sees, so two processes folding the same record draw
the same sheet (``docs/adr/0105``) — and, because the walk is over the enum
rather than over the weights, no weight is read on this side at all.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.engines.matchfit.core import ReliabilityStrand
from app.kernel import Instant
from app.modules.player_record.domain.record import ReliabilityPanel, StrandRow
from app.modules.player_score.domain.ports import PublishedScoreQuery


@final
class ScoreSubjectReliability:
    """The pill and the metered rows, in the record's own words."""

    def __init__(self, scores: PublishedScoreQuery) -> None:
        self._scores = scores

    async def reliability_of(
        self, player_id: UUID, *, now: Instant
    ) -> ReliabilityPanel | None:
        """What the platform watched of this one person, or nothing at all.

        ``now`` is handed down rather than read: both strands are facts about an
        instant — a game nobody recorded is played only once its entry window
        has closed, a seat has lapsed only once its day has run out — and every
        figure on one response is folded against one present.
        """

        published = await self._scores.scores_for([player_id], now=now)
        score = published.get(player_id)
        if score is None:
            return None
        return ReliabilityPanel(
            player_score=score.published,
            strands=tuple(
                StrandRow(
                    strand=strand,
                    good=ratio.good,
                    opportunities=ratio.opportunities,
                    # Copied, never divided. The one rounding of this record
                    # lives on the other side of the seam.
                    pct=ratio.value,
                )
                for strand in ReliabilityStrand
                if (ratio := score.strands.get(strand)) is not None
            ),
        )


__all__ = ["ScoreSubjectReliability"]
