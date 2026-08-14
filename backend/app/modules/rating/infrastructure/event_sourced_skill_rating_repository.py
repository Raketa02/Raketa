"""The Skill rating repository, over the event store.

The rating's half of what the assessment's repository already owns: which
aggregate-type string the streams are filed under, that state is rebuilt by
replaying them, what version the next append expects, and which stored key a
player's ratings are found by.

**Roughly fifteen lines here are near-identical to
``EventSourcedAssessmentRepository``, and that is deliberate.** ADR-0018 declined
a generic event-sourced base: event-sourced-versus-persisted-with-events is an
open per-context decision, and a shared base would quietly answer it for four
contexts that have not been built. Two concrete adapters that read straight
through are the cheaper mistake.

**The version is recovered, not taken**, so this must be constructed **per
request** from the session, exactly as the event store dependency is. A rating
this repository never read has no entry and is appended at version zero — "this
stream does not exist yet" follows from never having read it.

**The lookup key is the stored JSON payload of the opening event**, so it must
agree with ``RatingInitialised``'s serialized field name. A rename does not
raise: the query returns nothing, which is indistinguishable from an unrated
player — the ordinary answer for a new account.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.kernel import Sport
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating

RATING_AGGREGATE = "skill_rating"


def _opening_key(player_id: UUID) -> dict[str, str]:
    """What a rating stream's opening event must carry to be this player's.

    The key is ``RatingInitialised``'s field name as the codec writes it, and the
    value its primitive form.
    """

    return {"player_id": str(player_id)}


class EventSourcedSkillRatingRepository:
    """``SkillRatingRepository`` over ``DomainEventStore``."""

    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._event_store = event_store
        self._events = events
        # Aggregate id -> the stream version this request has seen. Read by
        # ``save`` as the expected version.
        self._versions: dict[UUID, int] = {}

    async def save(self, rating: SkillRating) -> None:
        pending = rating.pull_events()
        if not pending:
            return

        await self._event_store.append(
            aggregate_type=RATING_AGGREGATE,
            aggregate_id=rating.id,
            expected_version=self._versions.get(rating.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: completion writes this stream and the
        # assessment's in one transaction, and that boundary is the use case's.
        self._remember(rating)

    async def exists_for(self, *, player_id: UUID, sport: Sport) -> bool:
        # One lookup, not a scan: the stream id *is* the pair, so asking whether
        # the rating exists is asking whether that stream does. Nothing is
        # replayed and nothing is remembered — a caller that only asked a
        # question must not be able to save an aggregate it never read.
        stored = await self._event_store.load_stream(
            aggregate_type=RATING_AGGREGATE,
            aggregate_id=skill_rating_id(player_id, sport),
        )
        return bool(stored)

    async def find_all_for(self, *, player_id: UUID) -> list[SkillRating]:
        rating_ids = await self._event_store.find_aggregate_ids_by_first_event(
            aggregate_type=RATING_AGGREGATE,
            payload_equals=_opening_key(player_id),
        )

        ratings: list[SkillRating] = []
        for rating_id in rating_ids:
            stored = await self._event_store.load_stream(
                aggregate_type=RATING_AGGREGATE,
                aggregate_id=rating_id,
            )
            if not stored:
                continue
            rating = SkillRating.from_history(record.event for record in stored)
            # Registered like any read aggregate, so a rating that was found is a
            # rating that can be saved. Nothing transitions a rating today —
            # initialisation is its only event — so this guards the first
            # transition the match-update engine adds rather than a caller that
            # exists now.
            self._remember(rating)
            ratings.append(rating)
        return ratings

    def _remember(self, rating: SkillRating) -> None:
        self._versions[rating.id] = rating.version
