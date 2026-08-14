"""Create an assessment and hand back its opening question.

Starting is **idempotent per player and sport**: a start for a sport that already
has an unfinished run returns that run's outstanding question instead of opening a
second one. Without the guard a double-tapped confirm, or a retry after a response
that was lost in flight, opens two streams for one sport — and one of them is
stranded, because the in-progress lookup answers with a single run and the other
is then neither resumable nor abandonable through any client path.

The guard is scoped to runs that are *in progress*, never to any run that ever
existed: a sport whose previous run was **abandoned** still starts a genuinely
new one.

**A sport the player is already rated at is refused** (`SportAlreadyRated`,
409). A rating's stream is keyed by ``(player, sport)`` and initialisation is
its only transition, so a second completed run appends a second opening event to
a stream that already has one and the store rejects it — on the *last* answer,
after the whole questionnaire. Refusing the start is the only place where
refusing costs the player nothing, and it is checked **before** the in-progress
lookup so that a run stranded by that older behaviour cannot be resumed into the
same wall. Whether re-rating should instead replace the rating is deliberately
left open; the transition that would answer it is the match-update engine's
(#53).

**What this closes and what it does not.** The check is a read before a write, so
it resolves every case where the first start has already committed — the retry
after a lost response, the second device, the double tap slower than a round trip.
It does not serialise two starts that read the store *before either has appended*:
each mints its own stream id, so there is no version to collide on and both
succeed. Closing that needs a uniqueness the store can enforce — a projection
carrying one row per (player, sport, open run), or a stream id derived from those
— which is a schema decision rather than a guard, and is filed separately.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.engines.assessment import AskQuestion, AssessmentEngine
from app.modules.rating.application.assessment_view import (
    current_step,
    questions_asked,
)
from app.modules.rating.application.commands import (
    AssessmentStart,
    AssessmentStep,
    CreateAssessmentCommand,
)
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import SportAlreadyRated
from app.modules.rating.domain.ports import AssessmentRepository, SkillRatingRepository
from app.shared.clock import Clock
from app.shared.ids import new_uuid


class CreateAssessment:
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

    async def execute(self, command: CreateAssessmentCommand) -> AssessmentStart:
        # Asked first, and asked as a question rather than by loading anything.
        # A rated sport can produce no second rating, so opening a run for it —
        # or handing back one that is already open — only defers the failure to
        # the answer that would have finished it.
        if await self._ratings.exists_for(
            player_id=command.player_id,
            sport=command.sport,
        ):
            raise SportAlreadyRated()

        open_run = await self._assessments.find_open(
            player_id=command.player_id,
            sport=command.sport,
        )
        if open_run is not None:
            # Nothing is recorded: the run already exists and its outstanding
            # question is reproduced from the transcript, so a retry costs one
            # read and leaves the stream exactly as it was.
            return AssessmentStart(
                step=current_step(self._engine, open_run),
                created=False,
            )

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

        # Appended at version zero without saying so: the repository never
        # loaded this aggregate, so it has no version for it, and "this stream
        # does not exist yet" follows from that rather than from a claim here.
        await self._assessments.save(assessment)
        await self._uow.commit()

        return AssessmentStart(
            step=AssessmentStep(
                assessment_id=assessment_id,
                status=assessment.status.value,
                # Nothing has been answered yet, and the opening question does not
                # count itself — a fresh run reports 0 and the client shows 1.
                questions_asked=questions_asked(assessment),
                question=step.question,
                result=None,
            ),
            created=True,
        )
