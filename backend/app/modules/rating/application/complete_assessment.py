"""Complete a stopped assessment: create the Skill rating, and hand it back.

**This is the moment a rating comes into existence, and it is asked for.** Until
this slice it was a side effect of the last answer, which is what made
revisability vanish without warning: the confirm control's label is identical on
every question — necessarily, because the engine decides it has heard enough only
*after* an answer arrives — so a player tapped it on the last question exactly as
they had tapped it on the others and found their rating already made. Stopping
and completing are now two moments, and only the second is irreversible
(``docs/adr/0020``). What lives between them is the review.

**A stop is not stored, it is asked for.** ``next_step`` is a pure function of the
transcript, so *has this run stopped* is answered by running the engine over the
answers the stream already holds — the same determinism the outstanding question
and the served transcript already rest on. Nothing marks a stopped run, because a
mark would be a second representation of a fact the transcript already carries,
and the two would disagree the first time either moved.

**Completion is still one transaction, exactly as ADR-0017 requires**: the
assessment-completed event and the rating-initialised event are appended together
and the result returns inline, because the player sees their rating on the very
next screen. Only the trigger moved.

Completing twice recovers rather than conflicting. A submit that creates
something irreversible is precisely the control a player double-taps on a slow
connection, and a conflict there is one the client would have to translate back
into *you already have your rating* — so this does that itself, and answers the
second call with the same result the first returned.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.engines.assessment import AssessmentEngine
from app.kernel import Clock
from app.modules.rating.application.assessment_view import (
    current_step,
    questions_asked,
    served_transcript,
    stop_reached,
)
from app.modules.rating.application.commands import (
    AssessmentStep,
    CompleteAssessmentCommand,
)
from app.modules.rating.domain.errors import AssessmentNotStopped
from app.modules.rating.domain.ids import skill_rating_id
from app.modules.rating.domain.ports import AssessmentRepository, SkillRatingRepository
from app.modules.rating.domain.skill_rating import SkillRating


class CompleteAssessment:
    """Two aggregates move through repositories; the transaction stays here."""

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

    async def execute(self, command: CompleteAssessmentCommand) -> AssessmentStep:
        assessment = await self._assessments.load(
            command.assessment_id, for_player=command.player_id
        )

        if assessment.is_completed:
            # The same request arriving twice. Records nothing and answers with
            # the step the first call produced — ``current_step`` re-explains the
            # recorded numbers from the transcript, so the second response is the
            # first one, not a paraphrase of it.
            return current_step(self._engine, assessment)

        if not assessment.is_in_progress:
            # Abandoned: it never stopped, and there is no rating to hand back.
            raise AssessmentNotStopped()

        stop = stop_reached(self._engine, assessment)
        if stop is None:
            raise AssessmentNotStopped()

        now = self._clock.now()
        result = self._engine.finalize(
            sport=assessment.sport, transcript=assessment.transcript
        )
        # ``stop`` is passed through rather than discarded — the questionnaire's
        # last routing decision is recorded exactly as every earlier one is, and
        # it is the engine's own step so a reason cannot be filed beside a value
        # that did not cause it.
        assessment.complete(result=result, stop=stop, occurred_at=now)

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
