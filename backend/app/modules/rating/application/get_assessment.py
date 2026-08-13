"""Fetch a single assessment's current state.

Reading is pure replay: the stream is loaded, the aggregate reconstructed, and
its current step returned — the outstanding question, or the result if it is
finished. Nothing is written. A player can only see their own assessments; a
mismatch is indistinguishable from "does not exist".
"""

from __future__ import annotations

from app.application.ports import DomainEventStore
from app.engines.assessment import AssessmentEngine
from app.modules.rating.application.assessment_view import current_step
from app.modules.rating.application.commands import AssessmentStep, GetAssessmentQuery
from app.modules.rating.domain.assessment import Assessment
from app.modules.rating.domain.errors import AssessmentNotFound

ASSESSMENT_AGGREGATE = "assessment"


class GetAssessment:
    def __init__(
        self,
        *,
        engine: AssessmentEngine,
        event_store: DomainEventStore,
    ) -> None:
        self._engine = engine
        self._event_store = event_store

    async def execute(self, query: GetAssessmentQuery) -> AssessmentStep:
        stored = await self._event_store.load_stream(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=query.assessment_id,
        )
        if not stored:
            raise AssessmentNotFound()

        assessment = Assessment.from_history(record.event for record in stored)
        if assessment.player_id != query.player_id:
            raise AssessmentNotFound()

        return current_step(self._engine, assessment)
