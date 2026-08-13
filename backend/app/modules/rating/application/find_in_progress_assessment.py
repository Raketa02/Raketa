"""Find the assessment a player has in progress for a sport, if any.

This is what makes resume survive a force-quit, a reinstall and a new handset:
nothing about the transcript ever lived on the device, so the client asks the
server whether a run is already open. The lookup reads the streams directly —
every stream's opening event carries the player and sport it is keyed by — so no
device cache and no parallel index is involved. Each sport is fully isolated, so
a query for one sport can never surface another's.
"""

from __future__ import annotations

from app.application.ports import DomainEventStore
from app.engines.assessment import AssessmentEngine
from app.modules.rating.application.assessment_view import current_step
from app.modules.rating.application.commands import AssessmentStep, FindInProgressQuery
from app.modules.rating.domain.assessment import Assessment

ASSESSMENT_AGGREGATE = "assessment"


class FindInProgressAssessment:
    def __init__(
        self,
        *,
        engine: AssessmentEngine,
        event_store: DomainEventStore,
    ) -> None:
        self._engine = engine
        self._event_store = event_store

    async def execute(self, query: FindInProgressQuery) -> AssessmentStep | None:
        candidate_ids = await self._event_store.find_aggregate_ids_by_first_event(
            aggregate_type=ASSESSMENT_AGGREGATE,
            payload_equals={
                "player_id": str(query.player_id),
                "sport": query.sport.value,
            },
        )

        # Candidates are ordered oldest-first; the most recently opened run is the
        # one to resume, so scan from the newest end.
        for assessment_id in reversed(candidate_ids):
            stored = await self._event_store.load_stream(
                aggregate_type=ASSESSMENT_AGGREGATE,
                aggregate_id=assessment_id,
            )
            assessment = Assessment.from_history(record.event for record in stored)
            if assessment.is_in_progress:
                return current_step(self._engine, assessment)
        return None
