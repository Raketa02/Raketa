"""The Assessment repository, over the event store.

Everything a use case used to have to remember lives here: which aggregate-type
string the streams are filed under, that state is rebuilt by replaying them, that
the player must be checked before the aggregate is handed back, and what version
the next append expects.

**The version is recovered, not taken.** The adapter remembers the version of
every aggregate it loaded, so ``save`` knows what the stream looked like when the
caller read it. That is why it must be constructed **per request**, from the
session, exactly as the event store dependency is — an application-scoped
instance would carry one request's versions into another and append at a version
the stream has since passed. An aggregate this repository never loaded has no
entry and is therefore appended at version zero, which is how "this stream does
not exist yet" follows from never having read it rather than from a caller
saying so.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.kernel import Sport
from app.modules.rating.application.find_in_progress_assessment import (
    load_all_in_progress,
    load_in_progress,
)
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import AssessmentNotFound

ASSESSMENT_AGGREGATE = "assessment"


class EventSourcedAssessmentRepository:
    """``AssessmentRepository`` over ``DomainEventStore``."""

    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._event_store = event_store
        self._events = events
        # The identity map: aggregate id -> the stream version this request has
        # seen. Read by ``save`` as the expected version, and updated after every
        # append so a second save in the same request does not collide with the
        # first.
        self._versions: dict[UUID, int] = {}

    async def load(self, assessment_id: UUID, *, for_player: UUID) -> Assessment:
        stored = await self._event_store.load_stream(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=assessment_id,
        )
        if not stored:
            raise AssessmentNotFound()

        assessment = Assessment.from_history(record.event for record in stored)
        if assessment.player_id != for_player:
            # Another player's assessment is reported exactly as an absent one,
            # so the route cannot be used to discover which ids exist.
            raise AssessmentNotFound()

        self._remember(assessment)
        return assessment

    async def save(self, assessment: Assessment) -> None:
        pending = assessment.pull_events()
        if not pending:
            # Nothing decided anything: abandoning an already-abandoned run
            # lands here, and the retry succeeds without writing.
            return

        await self._event_store.append(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=assessment.id,
            expected_version=self._versions.get(assessment.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction spans two aggregates when an
        # assessment completes, so its boundary stays in the use case.
        self._remember(assessment)

    async def find_open(self, *, player_id: UUID, sport: Sport) -> Assessment | None:
        # The scan itself still lives in ``find_in_progress_assessment`` because
        # three use cases call it directly; #46 moves the body in here and
        # deletes the module-level functions, so the encoded lookup keys end up
        # with one home. Delegating rather than copying is what stops the two
        # having a chance to disagree in the meantime.
        assessment = await load_in_progress(
            self._event_store, player_id=player_id, sport=sport
        )
        if assessment is not None:
            self._remember(assessment)
        return assessment

    async def find_all_open(self, *, player_id: UUID) -> list[Assessment]:
        assessments = await load_all_in_progress(
            self._event_store, player_id=player_id
        )
        for assessment in assessments:
            self._remember(assessment)
        return assessments

    def _remember(self, assessment: Assessment) -> None:
        self._versions[assessment.id] = assessment.version
