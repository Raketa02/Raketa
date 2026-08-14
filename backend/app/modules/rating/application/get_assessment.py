"""Fetch a single assessment's current state.

Reading is pure replay, and the replay is the repository's: load the player's
assessment and return its current step — the outstanding question, or the result
if it is finished. Nothing is written.

A player can only see their own assessments, and asking for one requires saying
whose it is, so the guard cannot be forgotten here: an assessment that does not
exist and one belonging to somebody else raise the same error.
"""

from __future__ import annotations

from app.engines.assessment import AssessmentEngine
from app.modules.rating.application.assessment_view import current_step
from app.modules.rating.application.commands import AssessmentStep, GetAssessmentQuery
from app.modules.rating.domain.ports import AssessmentRepository


class GetAssessment:
    def __init__(
        self,
        *,
        engine: AssessmentEngine,
        assessments: AssessmentRepository,
    ) -> None:
        self._engine = engine
        self._assessments = assessments

    async def execute(self, query: GetAssessmentQuery) -> AssessmentStep:
        assessment = await self._assessments.load(
            query.assessment_id, for_player=query.player_id
        )
        return current_step(self._engine, assessment)
