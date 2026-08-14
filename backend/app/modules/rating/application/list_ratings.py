"""List the Skill ratings a player holds, one per sport they are rated at.

This answers *does this player have a rating* — the question the client's entry
gate turns on. It is deliberately **not** a flag on the user: onboarding is how a
Skill rating comes to exist, and a rating is per sport, so a player can be rated
at padel and unrated at tennis indefinitely. A per-player "onboarded" flag would
be a second, coarser truth about the same fact, and the two would disagree the
first time someone rated a second sport.

``GET /assessments/in-progress`` asks something genuinely different — whether a
*run* is unfinished. Neither substitutes for the other, and the gate needs both.

An unrated player is an empty collection, not a 404: absence of a rating is the
normal state of a new account, not an error.

The lookup lives on the repository, which is the only place that knows a rating
is a stream at all. Ordering is the order the ratings were earned.

**The aggregate is what comes back, not a view of it.** There used to be an
intermediate object here whose whole work was regrouping the range and the band
fields, and the module ran two policies for the same six facts: the result
response is built from an engine dataclass directly, while this one was built
from a hand copy. Presentation already imports engine dataclasses, so the
layering argument for the view was conceded long ago, and twenty-two field copies
between one producer and one consumer bought nothing. When the ratings projection
named in ADR-0017 arrives as a third consumer, it is the one that should decide
whether those six facts want a shared name.
"""

from __future__ import annotations

from app.modules.rating.application.commands import ListRatingsQuery
from app.modules.rating.domain.ports import SkillRatingRepository
from app.modules.rating.domain.skill_rating import SkillRating


class ListPlayerRatings:
    def __init__(self, *, ratings: SkillRatingRepository) -> None:
        self._ratings = ratings

    async def execute(self, query: ListRatingsQuery) -> list[SkillRating]:
        return await self._ratings.find_all_for(player_id=query.player_id)
