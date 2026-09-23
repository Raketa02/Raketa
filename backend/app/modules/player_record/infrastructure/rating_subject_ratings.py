"""``SubjectRatings`` over ``rating``'s published read. **A translation and no
arithmetic.**

The adapter lives in the *consumer's* infrastructure, which is this platform's
standing shape for a borrowed fact: a provider publishes what it knows about its
own subject, and the context that wants it in different words does the renaming
(``docs/adr/0159``). What crosses is the figures a rating already committed to
its own stream — the Level, the certainty, the range the engine rounded and the
band's published name — with the field names changed and nothing recomputed.

**The one thing that looks like a decision here is not one.** ``counted_games``
takes ``RatedSport.counted_results``, which is *how many confirmed counted
results have moved this Level*, and deliberately not ``games``' count of how many
counted games this person has played. They differ on two axes: the second is over
every sport, and it counts an evening two people never agreed a score for. What
the skill card claims is *what does this certainty rest on*, and the honest answer
to that is the results that actually moved it — a number that comes off the same
stream as the Level beside it and therefore moves in step with it
(``docs/adr/0139``).
"""

from __future__ import annotations

from typing import Mapping, final
from uuid import UUID

from app.kernel import Sport
from app.modules.player_record.domain.record import LikelyRange, SubjectRating
from app.modules.rating.domain.ports import RatedPlayerQuery


@final
class RatingSubjectRatings:
    """Every sport somebody is rated in, in this context's own words.

    It takes ``rating``'s read port and never its repository — which is the port
    existing for a reason rather than for symmetry: the repository remembers
    stream versions so a rating it found can be moved, and a sheet drawing a
    number has no business holding that. The narrowness is in the type, so it is
    real rather than promised.
    """

    def __init__(self, ratings: RatedPlayerQuery) -> None:
        self._ratings = ratings

    async def ratings_of(self, player_id: UUID) -> Mapping[Sport, SubjectRating]:
        held = await self._ratings.ratings_of(player_id)
        return {
            sport: SubjectRating(
                sport=sport,
                level=rating.mu,
                band=rating.band_name,
                confidence=rating.confidence,
                counted_games=rating.counted_results,
                likely_range=LikelyRange(
                    low=rating.range_low, high=rating.range_high
                ),
            )
            for sport, rating in held.items()
        }


__all__ = ["RatingSubjectRatings"]
