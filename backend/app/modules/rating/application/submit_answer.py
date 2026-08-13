"""Submit an answer and receive the next question, or the final result.

Idempotency comes from the domain, not a header. An answer is accepted only for
the question currently outstanding; re-submitting the just-answered question
records nothing and returns the current state; any other question conflicts.
Optimistic concurrency on the event store makes a genuine double-submit fail
loudly.

Completion is one transaction: the assessment-completed event and the
rating-initialised event are appended together and the result returns inline,
because the player sees their rating on the very next screen.
"""

from __future__ import annotations

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.engines.assessment import AskQuestion, AssessmentEngine, Question
from app.modules.rating.application.assessment_view import completed_result
from app.modules.rating.application.commands import (
    AssessmentStep,
    SubmitAnswerCommand,
)
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import (
    AssessmentNotFound,
    InvalidAnswerOption,
    QuestionNotOutstanding,
)
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.skill_rating import SkillRating
from app.shared.clock import Clock

ASSESSMENT_AGGREGATE = "assessment"
RATING_AGGREGATE = "skill_rating"


class SubmitAnswer:
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

    async def execute(self, command: SubmitAnswerCommand) -> AssessmentStep:
        stored = await self._event_store.load_stream(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=command.assessment_id,
        )
        if not stored:
            raise AssessmentNotFound()

        assessment = Assessment.from_history(record.event for record in stored)
        if assessment.player_id != command.player_id:
            # A player can only see and act on their own assessments; a mismatch
            # is indistinguishable from "does not exist".
            raise AssessmentNotFound()

        base_version = assessment.version

        # Idempotent replay of the just-answered question: record nothing, return
        # the current state. A lost response can never double-record.
        if command.question_id == assessment.last_answered_question_id:
            return self._current_state(assessment)

        if command.question_id != assessment.outstanding_question_id:
            raise QuestionNotOutstanding()

        outstanding = self._reproduce_outstanding(assessment)
        if command.option_id not in {option.id for option in outstanding.options}:
            raise InvalidAnswerOption()

        now = self._clock.now()
        assessment.answer(
            question_id=command.question_id,
            option_id=command.option_id,
            occurred_at=now,
        )

        step = self._engine.next_step(
            sport=assessment.sport, transcript=assessment.transcript
        )
        if isinstance(step, AskQuestion):
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
                aggregate_id=assessment.id,
                expected_version=base_version,
                events=pending,
            )
            await self._events.publish_many(pending)
            await self._uow.commit()
            return AssessmentStep(
                assessment_id=assessment.id,
                status=assessment.status.value,
                question=step.question,
                result=None,
            )

        # The engine is done: complete the assessment and initialise the rating,
        # both appended in the same transaction.
        result = self._engine.finalize(
            sport=assessment.sport, transcript=assessment.transcript
        )
        assessment.complete(result=result, occurred_at=now)
        assessment_events = assessment.pull_events()

        rating = SkillRating.initialise(
            rating_id=skill_rating_id(assessment.player_id, assessment.sport),
            player_id=assessment.player_id,
            sport=assessment.sport,
            result=result,
            source_assessment_id=assessment.id,
            occurred_at=now,
        )
        rating_events = rating.pull_events()

        await self._event_store.append(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=assessment.id,
            expected_version=base_version,
            events=assessment_events,
        )
        await self._event_store.append(
            aggregate_type=RATING_AGGREGATE,
            aggregate_id=rating.id,
            expected_version=0,
            events=rating_events,
        )
        await self._events.publish_many([*assessment_events, *rating_events])
        await self._uow.commit()

        return AssessmentStep(
            assessment_id=assessment.id,
            status=assessment.status.value,
            question=None,
            result=result,
        )

    def _current_state(self, assessment: Assessment) -> AssessmentStep:
        if assessment.is_completed:
            return AssessmentStep(
                assessment_id=assessment.id,
                status=assessment.status.value,
                question=None,
                # The same explained result the first response carried, so a
                # retried submission is indistinguishable from the original.
                result=completed_result(self._engine, assessment),
            )
        return AssessmentStep(
            assessment_id=assessment.id,
            status=assessment.status.value,
            question=self._reproduce_outstanding(assessment),
            result=None,
        )

    def _reproduce_outstanding(self, assessment: Assessment) -> Question:
        # The engine is deterministic, so the outstanding question is exactly the
        # question it returns for the answered transcript — no need to store the
        # question copy, the version's code *is* the question definition.
        step = self._engine.next_step(
            sport=assessment.sport, transcript=assessment.transcript
        )
        assert isinstance(step, AskQuestion)
        return step.question
