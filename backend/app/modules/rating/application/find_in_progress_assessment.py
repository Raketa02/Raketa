"""Find the assessment a player has in progress for a sport, if any.

This is what makes resume survive a force-quit, a reinstall and a new handset:
nothing about the transcript ever lived on the device, so the client asks the
server whether a run is already open. The lookup reads the streams directly —
every stream's opening event carries the player and sport it is keyed by — so no
device cache and no parallel index is involved. Each sport is fully isolated, so
a query for one sport can never surface another's.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventStore
from app.engines.assessment import AssessmentEngine
from app.kernel import Sport
from app.modules.rating.application.assessment_view import current_step
from app.modules.rating.application.commands import AssessmentStep, FindInProgressQuery
from app.modules.rating.domain.assessment import Assessment

ASSESSMENT_AGGREGATE = "assessment"


async def load_in_progress(
    event_store: DomainEventStore,
    *,
    player_id: UUID,
    sport: Sport,
) -> Assessment | None:
    """The player's unfinished run for a sport, replayed, or nothing.

    One owner for the question "is a run already open here", because two callers
    ask it for opposite reasons: this module answers *resume*, and
    ``create_assessment`` asks it to avoid opening a second run. A second copy of
    the scan would be a second place for "in progress" to drift.
    """

    candidate_ids = await event_store.find_aggregate_ids_by_first_event(
        aggregate_type=ASSESSMENT_AGGREGATE,
        payload_equals={
            "player_id": str(player_id),
            "sport": sport.value,
        },
    )

    # Candidates are ordered oldest-first; the most recently opened run is the
    # one to resume, so scan from the newest end.
    for assessment_id in reversed(candidate_ids):
        stored = await event_store.load_stream(
            aggregate_type=ASSESSMENT_AGGREGATE,
            aggregate_id=assessment_id,
        )
        assessment = Assessment.from_history(record.event for record in stored)
        if assessment.is_in_progress:
            return assessment
    return None


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
        assessment = await load_in_progress(
            self._event_store,
            player_id=query.player_id,
            sport=query.sport,
        )
        if assessment is None:
            return None
        return current_step(self._engine, assessment)
