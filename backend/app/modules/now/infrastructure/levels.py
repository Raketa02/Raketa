"""``Levels`` over the rating context's own repository.

The one place in Now that knows a Level is a ``SkillRating``'s μ and that a
*questionnaire-derived* rating is one still wearing the status a questionnaire
produces. It takes the **port**, not the adapter, on the precedent
``RatedSportsFromSkillRatings`` set: what backs a rating is the rating context's
business, and the day a projection answers this faster than a replay does, only
the composition root moves.

**One read per player, by the pair.** ``find_all_for`` replays every rating a
player holds to answer a question about one sport; the stream id *is* the pair,
so asking for the pair is one stream load and no index read. The shelf asks
about the viewer and up to eight candidates, so the difference is the whole cost
of the shelf on a player rated at four sports.

**Absent is absent.** A player with no rating at this sport is missing from the
answer rather than present at some imputed number: the shelf's whole order is one
subtraction between two Levels, and a zero on either side is an order computed
from a fact nobody holds.
"""

from __future__ import annotations

from typing import Mapping, Sequence
from uuid import UUID

from app.engines.assessment import STATUS_INITIAL_ESTIMATE
from app.kernel import Sport

from app.modules.now.domain.ports import Levels
from app.modules.now.domain.screen import Level
from app.modules.rating.domain.ports import SkillRatingRepository


class LevelsFromSkillRatings(Levels):
    """Each player's Level at one sport, and whether answers are all of it."""

    def __init__(self, ratings: SkillRatingRepository) -> None:
        self._ratings = ratings

    async def at(
        self, *, sport: Sport, players: Sequence[UUID]
    ) -> Mapping[UUID, Level]:
        found: dict[UUID, Level] = {}
        for player in players:
            if player in found:
                # The viewer can be in her own candidate list on a shelf she is
                # filtered out of later, and a repeated id is one stream replay
                # too many on the busiest read in the product.
                continue
            rating = await self._ratings.find_for(player_id=player, sport=sport)
            if rating is None:
                continue
            found[player] = Level(
                value=rating.mu,
                # The **quiet marker**, and it is a comparison against the shared
                # engine vocabulary rather than against a string spelled here:
                # a reader holding its own copy of a status is a reader that
                # stops agreeing with the engine the day one is retuned, in the
                # direction of telling a player a questionnaire number is a
                # played one.
                provisional=rating.status == STATUS_INITIAL_ESTIMATE,
            )
        return found
