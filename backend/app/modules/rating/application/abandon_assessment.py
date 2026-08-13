"""Abandon an in-progress assessment.

Abandonment is a state transition, not a deletion: an ``AssessmentAbandoned``
event is appended to the stream, which ends that run and frees the sport to be
started again. Any other sport's assessment is a different stream and is left
untouched. A completed assessment cannot be abandoned — its rating already
exists; abandoning an already-abandoned one is a no-op so a retry cannot fail.
"""

from __future__ import annotations

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.modules.rating.application.commands import AbandonAssessmentCommand
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import AssessmentNotFound
from app.shared.clock import Clock

ASSESSMENT_AGGREGATE = "assessment"


class AbandonAssessment:
    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        uow: UnitOfWork,
        clock: Clock,
        events: DomainEventPublisher,
    ) -> None:
        self._event_store = event_store
        self._uow = uow
        self._clock = clock
        self._events = events

    async def execute(self, command: AbandonAssessmentCommand) -> None:
        stored = await self._event_store.load_stream(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=command.assessment_id,
        )
        if not stored:
            raise AssessmentNotFound()

        assessment = Assessment.from_history(record.event for record in stored)
        if assessment.player_id != command.player_id:
            raise AssessmentNotFound()

        base_version = assessment.version
        assessment.abandon(occurred_at=self._clock.now())

        pending = assessment.pull_events()
        if not pending:
            # Already abandoned: nothing to record, and the retry succeeds.
            return

        await self._event_store.append(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=assessment.id,
            expected_version=base_version,
            events=pending,
        )
        await self._events.publish_many(pending)
        await self._uow.commit()
