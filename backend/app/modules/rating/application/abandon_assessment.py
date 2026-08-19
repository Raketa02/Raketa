"""Abandon an in-progress assessment.

Abandonment is a state transition, not a deletion: an ``AssessmentAbandoned``
event is appended to the stream, which ends that run and frees the sport to be
started again. Any other sport's assessment is a different stream and is left
untouched. A completed assessment cannot be abandoned — its rating already
exists; abandoning an already-abandoned one is a no-op so a retry cannot fail.

The no-op is the repository's: ``save`` writes nothing when the aggregate
recorded nothing, so this use case does not check first.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.rating.application.commands import AbandonAssessmentCommand
from app.modules.rating.domain.ports import AssessmentRepository


class AbandonAssessment:
    def __init__(
        self,
        *,
        assessments: AssessmentRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._assessments = assessments
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AbandonAssessmentCommand) -> None:
        assessment = await self._assessments.load(
            command.assessment_id, for_player=command.player_id
        )
        assessment.abandon(occurred_at=self._clock.now())
        await self._assessments.save(assessment)
        await self._uow.commit()
