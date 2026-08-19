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

**The guard is a read before a write, and it is no longer the only thing holding
the line.** It resolves every case where the first start has already committed —
the retry after a lost response, the second device, the double tap slower than a
round trip — and it does so without writing anything.

What it never could resolve is two starts that read the store *before either has
appended*. While each minted a random stream id there was nothing for them to
collide on, so both succeeded and one run was stranded: invisible to every client
path, so nothing surfaced it and nothing cleaned it up (#35).

**The stream id is now derived from (player, sport, attempt)**, so those two
starts compute the *same* id and collide on version 1 of one stream. The store
already enforces that — ``uq_event_store_stream_version`` has been on the table
since it was created — so this needs no projection, no migration and no rule for
who maintains one. The loser rolls back and re-reads: if the winner has committed
it hands back that run, exactly as the ordinary retry does; if it has not, the
conflict surfaces as a 409 the client can retry into the same answer. Either way
**no second stream is ever opened**, which is the part that was permanent.
"""

from __future__ import annotations

from app.application.events.store import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.engines.assessment import AskQuestion, AssessmentEngine
from app.kernel import Clock
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
        # Derived, not minted: see the module docstring. A concurrent start
        # computes this same id, which is what gives the store something to
        # reject.
        assessment_id = await self._assessments.next_identity(
            player_id=command.player_id,
            sport=command.sport,
        )

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
        try:
            await self._assessments.save(assessment)
            await self._uow.commit()
        except EventStreamVersionConflict as conflict:
            return await self._yield_to_the_winner(command, conflict)

        return AssessmentStart(
            step=AssessmentStep(
                assessment_id=assessment_id,
                status=assessment.status.value,
                # Nothing has been answered yet, and the opening question does not
                # count itself — a fresh run reports 0 and the client shows 1. The
                # transcript is empty for the same reason, and is served empty
                # rather than left out: a client reads one shape on every step.
                questions_asked=questions_asked(assessment),
                transcript=(),
                question=step.question,
                result=None,
            ),
            created=True,
        )

    async def _yield_to_the_winner(
        self,
        command: CreateAssessmentCommand,
        conflict: EventStreamVersionConflict,
    ) -> AssessmentStart:
        """Another start reached this stream first. Hand back its run, or say so.

        The transaction is rolled back before anything is re-read: the append
        failed inside it, and a session that has raised is not a session you can
        keep querying.

        If the winner has committed, its run is found and returned exactly as the
        ordinary retry returns it — the player cannot tell the two apart, and
        should not be able to. If it has not committed yet, there is nothing
        truthful to hand back, so the conflict is re-raised and surfaces as a 409
        the client retries into the same answer a moment later. What does **not**
        happen either way is a second stream, which is the failure that was
        silent and permanent.
        """

        await self._uow.rollback()

        winner = await self._assessments.find_open(
            player_id=command.player_id,
            sport=command.sport,
        )
        if winner is None:
            raise conflict

        return AssessmentStart(
            step=current_step(self._engine, winner),
            created=False,
        )
