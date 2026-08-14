"""Submit an answer and receive the next question, or the final result.

Idempotency comes from the domain, not a header. An answer is accepted only for
the question currently outstanding; re-submitting the just-answered question
records nothing and returns the current state; any other question conflicts.
Optimistic concurrency on the event store makes a genuine double-submit fail
loudly.

That replay answers with ``assessment_view.current_step`` — the same function the
read route uses, deliberately rather than a copy of it. The replay branch is
guarded on the question id alone, and abandonment clears the outstanding question
while leaving the last-answered id where it was, so a replay can arrive after the
run has ended. A private copy of this logic that had never grown an abandoned
case answered that replay with a question for a run the server considered over,
and the two routes described one run differently.

Both aggregates are loaded and saved through their repositories, so the ownership
guard, the aggregate-type strings and the versions these appends expect are no
longer things this use case has to remember — asking for the aggregate means
saying whose it is.

Completion is one transaction: the assessment-completed event and the
rating-initialised event are appended together and the result returns inline,
because the player sees their rating on the very next screen.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.engines.assessment import AskQuestion, AssessmentEngine
from app.modules.rating.application.assessment_view import (
    current_step,
    outstanding_question,
    questions_asked,
)
from app.modules.rating.application.commands import (
    AssessmentStep,
    SubmitAnswerCommand,
)
from app.modules.rating.domain.errors import (
    InvalidAnswerOption,
    QuestionNotOutstanding,
)
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.ports import AssessmentRepository, SkillRatingRepository
from app.modules.rating.domain.skill_rating import SkillRating
from app.shared.clock import Clock


class SubmitAnswer:
    """Both aggregates move through repositories; the transaction stays here."""

    def __init__(
        self,
        *,
        engine: AssessmentEngine,
        assessments: AssessmentRepository,
        ratings: SkillRatingRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._engine = engine
        self._assessments = assessments
        self._ratings = ratings
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SubmitAnswerCommand) -> AssessmentStep:
        assessment = await self._assessments.load(
            command.assessment_id, for_player=command.player_id
        )

        # Idempotent replay of the just-answered question: record nothing, return
        # the current state. A lost response can never double-record.
        if command.question_id == assessment.last_answered_question_id:
            return current_step(self._engine, assessment)

        if command.question_id != assessment.outstanding_question_id:
            raise QuestionNotOutstanding()

        outstanding = outstanding_question(self._engine, assessment)
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
            await self._assessments.save(assessment)
            await self._uow.commit()
            return AssessmentStep(
                assessment_id=assessment.id,
                status=assessment.status.value,
                # The answer just recorded is in the transcript, so this response
                # already counts it — the next question is one further along.
                questions_asked=questions_asked(assessment),
                question=step.question,
                result=None,
            )

        # The engine is done: complete the assessment and initialise the rating,
        # both appended in the same transaction. ``step`` is the stop itself, and
        # it is passed through rather than discarded — the questionnaire's last
        # routing decision is recorded exactly as every earlier one is.
        result = self._engine.finalize(
            sport=assessment.sport, transcript=assessment.transcript
        )
        assessment.complete(result=result, stop=step, occurred_at=now)

        rating = SkillRating.initialise(
            rating_id=skill_rating_id(assessment.player_id, assessment.sport),
            player_id=assessment.player_id,
            sport=assessment.sport,
            result=result,
            source_assessment_id=assessment.id,
            occurred_at=now,
        )

        # Two streams, one transaction. Neither ``save`` commits, so the boundary
        # stays here — ADR-0017 states the single transaction as a domain rule
        # rather than a persistence detail. The assessment is saved first because
        # the outbox takes them in the order they happened.
        await self._assessments.save(assessment)
        await self._ratings.save(rating)
        await self._uow.commit()

        return AssessmentStep(
            assessment_id=assessment.id,
            status=assessment.status.value,
            # Equal to the result's own count by construction: both are the length
            # of this transcript, so the run's number does not jump as it finishes.
            questions_asked=questions_asked(assessment),
            question=None,
            result=result,
        )

