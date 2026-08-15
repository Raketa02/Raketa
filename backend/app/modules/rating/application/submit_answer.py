"""Submit an answer and receive the next question, or the final result.

**One submission, three meanings, decided by what the transcript already holds**
(``docs/adr/0020``). The question is either unanswered — in which case this is an
answer, and it is accepted only for the question currently outstanding — or it is
already answered, in which case the option decides: a *different* option is a
**revision**, and the option already recorded is a **replay**. Anything else
conflicts.

Reading the transcript rather than only the last-answered id is what makes the
middle case reachable at all, and it subsumes what the id used to do: a replay is
now a replay of any answer, not only of the most recent one.

Idempotency still comes from the domain, not a header. A replay records nothing
and answers with ``assessment_view.current_step`` — the same function the read
route uses, deliberately rather than a copy of it. Abandonment clears the
outstanding question while leaving the transcript where it is, so a replay can
arrive after the run has ended; a private copy of this logic that had never grown
an abandoned case answered that replay with a question for a run the server
considered over, and the two routes described one run differently. Optimistic
concurrency on the event store makes a genuine double-submit — or two devices
revising at once — fail loudly rather than interleave.

**A revision truncates and replays, and that is what makes it free.** The
aggregate discards every answer after the revised one, because each was pitched
at a difficulty chosen from the estimate as it then stood; the engine is then
asked what to do with the resulting transcript, by exactly the code an ordinary
answer runs. Since ``next_step`` and ``finalize`` are pure functions of the
transcript, a truncated transcript is simply a transcript — so a revision can ask
another question, or stop the run, and neither is a special case here.

Both aggregates are loaded and saved through their repositories, so the ownership
guard, the aggregate-type strings and the versions these appends expect are no
longer things this use case has to remember — asking for the aggregate means
saying whose it is.

Completion is one transaction: the assessment-completed event and the
rating-initialised event are appended together and the result returns inline,
because the player sees their rating on the very next screen.
"""

from __future__ import annotations

from datetime import datetime

from app.application.ports import UnitOfWork
from app.engines.assessment import AskQuestion, AssessmentEngine
from app.modules.rating.application.assessment_view import (
    current_step,
    outstanding_question,
    questions_asked,
    served_transcript,
)
from app.modules.rating.application.commands import (
    AssessmentStep,
    SubmitAnswerCommand,
)
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import (
    AnswerNoLongerRevisable,
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

        recorded = assessment.recorded_option(command.question_id)
        if recorded is not None:
            # Idempotent replay: the option already recorded, submitted again.
            # A lost response retried, or a player who changed their mind and
            # changed it back — one is a network fact and the other a human one,
            # and neither is a decision the stream needs to hold. Record nothing
            # and return the current state.
            if recorded == command.option_id:
                return current_step(self._engine, assessment)
            return await self._revise(assessment, command)

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
        return await self._advance(assessment, now)

    async def _revise(
        self, assessment: Assessment, command: SubmitAnswerCommand
    ) -> AssessmentStep:
        """Change an answer already given, then continue from the truncated run.

        The two refusals above the change are ordered by what the client can do
        about them. A finished run's answers are settled and there is no question
        to re-render, so it gets its own code; an abandoned one has no rating to
        show and refetching is the whole recovery, so it gets the ordinary
        conflict — which is also what any submission to an abandoned run has
        always got.
        """

        if assessment.is_completed:
            raise AnswerNoLongerRevisable()
        if not assessment.is_in_progress:
            raise QuestionNotOutstanding()

        # The question as it was put to the player, which is the only thing that
        # can say which options it offered. Taken from the served transcript
        # rather than reproduced here, so the one rule about reproducing a past
        # question keeps one implementation — including its refusal to speak for
        # an engine version that has been retired, which is why an entry can be
        # missing for a question the transcript holds.
        asked = next(
            (
                entry
                for entry in served_transcript(self._engine, assessment)
                if entry.question.id == command.question_id
            ),
            None,
        )
        if asked is None:
            raise QuestionNotOutstanding()
        if command.option_id not in {option.id for option in asked.question.options}:
            raise InvalidAnswerOption()

        now = self._clock.now()
        assessment.revise(
            question_id=command.question_id,
            option_id=command.option_id,
            occurred_at=now,
        )
        return await self._advance(assessment, now)

    async def _advance(self, assessment: Assessment, now: datetime) -> AssessmentStep:
        """Ask the engine what this transcript wants next, and persist the answer.

        Shared by answering and revising deliberately: the engine is a pure
        function of the transcript, so *how* the transcript reached its current
        shape is not something this code is entitled to branch on. A revision
        that stops the run therefore completes it by the same path an ordinary
        last answer does.
        """

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
                # already counts it — the next question is one further along, and
                # the served transcript ends with the answer that produced it.
                questions_asked=questions_asked(assessment),
                transcript=served_transcript(self._engine, assessment),
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
            # The evidence the result was computed from, served beside it. A
            # finished run's transcript is still the answers the player gave.
            transcript=served_transcript(self._engine, assessment),
            question=None,
            result=result,
        )
