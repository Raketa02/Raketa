"""``Ratings`` over the rating context's own repository, in the engines' words.

The second of two shapes one stored fact takes on this screen, and the split is
deliberate. ``Levels`` answers what a **card** prints — a number and the quiet
marker saying whether a questionnaire is all the evidence there is. This answers
what an **engine** reads — a Level, an Uncertainty and a Confidence, arriving
together or not at all, because a forecast propagates σ and a card never shows
one. Neither is derivable from the other without inventing the half it drops.

**One read, by the pair.** The stream id *is* ``(player, sport)``, so this is one
stream load where ``find_all_for`` would replay every rating she holds to answer
a question about one sport.

**Absent is absent.** A player with no rating at this sport gets ``None`` and
never a Level standing in for one: the viewer's own answer decides whether she can
be ranked at all, and a stand-in there would rank her list against a number
nobody holds.
"""

from __future__ import annotations

from uuid import UUID

from app.engines.matchmaking import (
    HUNDREDTHS,
    Occupant,
    PlayerRef,
    PlayerSkill,
    level,
    uncertainty,
)
from app.kernel import Sport

from app.modules.rating.domain.ports import SkillRatingRepository


class RatingsFromSkillRatings:
    """One player's rating at one sport, as an ``Occupant`` or as nothing."""

    def __init__(self, ratings: SkillRatingRepository) -> None:
        self._ratings = ratings

    async def occupant(self, *, player_id: UUID, sport: Sport) -> Occupant | None:
        rating = await self._ratings.find_for(player_id=player_id, sport=sport)
        if rating is None:
            return None
        # The one crossing from the rating context's float into the engines'
        # exact ratio: ``Level`` is a ``Fraction``, and ``Fraction(0.9)`` is the
        # double nearest nine tenths rather than nine tenths. Hundredths are the
        # rating scale's own resolution — μ 3,20 is ``level(320)``.
        return PlayerSkill(
            player=PlayerRef(str(player_id)),
            level=level(round(rating.mu * HUNDREDTHS)),
            uncertainty=uncertainty(round(rating.sigma * HUNDREDTHS)),
            confidence=rating.confidence,
        )
