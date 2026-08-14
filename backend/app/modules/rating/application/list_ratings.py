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

The lookup reads the streams directly, exactly as the in-progress lookup does —
every rating stream's opening event carries the player it is keyed by, so no
parallel index is involved. Ordering is the order the ratings were earned, which
is what the store's oldest-first ids already give.
"""

from __future__ import annotations

from app.application.ports import DomainEventStore
from app.modules.rating.application.commands import ListRatingsQuery, RatingView
from app.modules.rating.domain.skill_rating import SkillRating

RATING_AGGREGATE = "skill_rating"


class ListPlayerRatings:
    def __init__(self, *, event_store: DomainEventStore) -> None:
        self._event_store = event_store

    async def execute(self, query: ListRatingsQuery) -> list[RatingView]:
        rating_ids = await self._event_store.find_aggregate_ids_by_first_event(
            aggregate_type=RATING_AGGREGATE,
            payload_equals={"player_id": str(query.player_id)},
        )

        ratings: list[RatingView] = []
        for rating_id in rating_ids:
            stored = await self._event_store.load_stream(
                aggregate_type=RATING_AGGREGATE,
                aggregate_id=rating_id,
            )
            ratings.append(_to_view(SkillRating.from_history(r.event for r in stored)))
        return ratings


def _to_view(rating: SkillRating) -> RatingView:
    # The band travels as the engine computed it. Its boundaries are deliberately
    # uneven and were wrong once already, so nothing downstream may restate them.
    return RatingView(
        sport=rating.sport,
        mu=rating.mu,
        sigma=rating.sigma,
        confidence=rating.confidence,
        range_low=rating.range_low,
        range_high=rating.range_high,
        band_name=rating.band_name,
        band_lower=rating.band_lower,
        band_upper=rating.band_upper,
        status=rating.status,
        engine_version=rating.engine_version,
        updated_at=rating.updated_at,
    )
