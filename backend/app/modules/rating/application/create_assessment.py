"""Create an assessment and hand back its opening question."""

from __future__ import annotations

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.engines.assessment import AskQuestion, AssessmentEngine
from app.modules.rating.application.commands import (
    AssessmentStep,
    CreateAssessmentCommand,
)
from app.modules.rating.domain.assessment import Assessment
from app.shared.clock import Clock
from app.shared.ids import new_uuid

ASSESSMENT_AGGREGATE = "assessment"


class CreateAssessment:
    def __init__(
        self,
        *,
        engine: AssessmentEngine,
        event_store: DomainEventStore,
        uow: UnitOfWork,
        clock: Clock,
        events: DomainEventPublisher,
    ) -> None:
        self._engine = engine
        self._event_store = event_store
        self._uow = uow
        self._clock = clock
        self._events = events

    async def execute(self, command: CreateAssessmentCommand) -> AssessmentStep:
        now = self._clock.now()
        assessment_id = new_uuid()

        # A fresh assessment always opens with a question; the engine reports why
        # it asked and the estimate that existed at that moment (the prior).
        step = self._engine.next_step(sport=command.sport, transcript=())
        assert isinstance(step, AskQuestion)

        assessment = Assessment.start(
            assessment_id=assessment_id,
            player_id=command.player_id,
            sport=command.sport,
            engine_version=self._engine.version,
            occurred_at=now,
        )
        assessment.ask(
            question_id=step.question.id,
            reason=step.reason,
            mu=step.mu,
            sigma=step.sigma,
            occurred_at=now,
        )

        pending = assessment.pull_events()
        await self._event_store.append(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=assessment_id,
            expected_version=0,
            events=pending,
        )
        await self._events.publish_many(pending)
        await self._uow.commit()

        return AssessmentStep(
            assessment_id=assessment_id,
            status=assessment.status.value,
            question=step.question,
            result=None,
        )
