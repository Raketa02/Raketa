"""Create an assessment and hand back its opening question.

Starting is **idempotent per player and sport**: a start for a sport that already
has an unfinished run returns that run's outstanding question instead of opening a
second one. Without the guard a double-tapped confirm, or a retry after a response
that was lost in flight, opens two streams for one sport — and one of them is
stranded, because the in-progress lookup answers with a single run and the other
is then neither resumable nor abandonable through any client path.

The guard is scoped to runs that are *in progress*, never to any run that ever
existed: a sport whose previous run was completed or abandoned still starts a
genuinely new one.

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

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.engines.assessment import AskQuestion, AssessmentEngine
from app.modules.rating.application.assessment_view import current_step
from app.modules.rating.application.commands import (
    AssessmentStart,
    AssessmentStep,
    CreateAssessmentCommand,
)
from app.modules.rating.application.find_in_progress_assessment import load_in_progress
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

    async def execute(self, command: CreateAssessmentCommand) -> AssessmentStart:
        open_run = await load_in_progress(
            self._event_store,
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

        pending = assessment.pull_events()
        await self._event_store.append(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=assessment_id,
            expected_version=0,
            events=pending,
        )
        await self._events.publish_many(pending)
        await self._uow.commit()

        return AssessmentStart(
            step=AssessmentStep(
                assessment_id=assessment_id,
                status=assessment.status.value,
                question=step.question,
                result=None,
            ),
            created=True,
        )
