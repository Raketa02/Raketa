"""Find the assessments a player has in progress — for one sport, or for all.

This is what makes resume survive a force-quit, a reinstall and a new handset:
nothing about the transcript ever lived on the device, so the client asks the
server whether a run is already open. The lookup reads the streams directly —
every stream's opening event carries the player and sport it is keyed by — so no
device cache and no parallel index is involved. Each sport is fully isolated, so
a query for one sport can never surface another's.

Two shapes, because the client asks the question two ways. Resuming a sport it
has already chosen is a question about that sport. The entry gate's question —
*is any run unfinished* — is about the player, and asking it one sport at a time
cost four requests on every cold launch for an answer that is almost always
"no".
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventStore
from app.engines.assessment import AssessmentEngine
from app.kernel import Sport
from app.modules.rating.application.assessment_view import current_step
from app.modules.rating.application.commands import (
    AssessmentStep,
    FindInProgressQuery,
    InProgressAssessmentView,
    ListInProgressQuery,
)
from app.modules.rating.domain.assessment import Assessment

ASSESSMENT_AGGREGATE = "assessment"


async def _replay(event_store: DomainEventStore, assessment_id: UUID) -> Assessment:
    stored = await event_store.load_stream(
        aggregate_type=ASSESSMENT_AGGREGATE,
        aggregate_id=assessment_id,
    )
    return Assessment.from_history(record.event for record in stored)


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
        assessment = await _replay(event_store, assessment_id)
        if assessment.is_in_progress:
            return assessment
    return None


async def load_all_in_progress(
    event_store: DomainEventStore,
    *,
    player_id: UUID,
) -> list[Assessment]:
    """Every sport's unfinished run for this player, at most one per sport.

    The same scan as ``load_in_progress`` with the sport left off the key, so it
    answers for every sport at once. "At most one per sport" and "the newest
    wins" are the singular form's rules, kept deliberately identical: the two
    reads answer the same question about the same player, and a gate that routed
    to one run while the resume read offered another would be a bug the client
    could not see. Scanning newest-first and keeping the first run seen for each
    sport is what makes them agree.

    Ordered by the sport registry (``Sport``'s own order), so a caller that wants
    one run — the entry gate wants exactly one — can take the first entry and get
    a stable answer rather than one that depends on which sport was started
    first.

    This replays every assessment stream the player has ever opened, finished and
    abandoned ones included, exactly as ``list_ratings`` replays every rating.
    That is the cost of reading an event-sourced store without a projection; a
    player's streams are counted in tens, and the alternative is a second place
    holding a fact the streams already hold.
    """

    candidate_ids = await event_store.find_aggregate_ids_by_first_event(
        aggregate_type=ASSESSMENT_AGGREGATE,
        payload_equals={"player_id": str(player_id)},
    )

    open_by_sport: dict[Sport, Assessment] = {}
    for assessment_id in reversed(candidate_ids):
        assessment = await _replay(event_store, assessment_id)
        if assessment.is_in_progress and assessment.sport not in open_by_sport:
            open_by_sport[assessment.sport] = assessment
    return [open_by_sport[sport] for sport in Sport if sport in open_by_sport]


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


class ListInProgressAssessments:
    """Which of this player's assessments are unfinished, across every sport.

    No engine, and that is the point. An entry carries the assessment id and its
    sport — what a router needs to route — and nothing the engine would have to
    be run to produce. The common answer is an empty collection, and it would be
    a poor trade to make every cold launch reproduce four outstanding questions
    so that the rare launch which resumes one need not re-read it.
    """

    def __init__(self, *, event_store: DomainEventStore) -> None:
        self._event_store = event_store

    async def execute(
        self, query: ListInProgressQuery
    ) -> list[InProgressAssessmentView]:
        open_runs = await load_all_in_progress(
            self._event_store, player_id=query.player_id
        )
        return [
            InProgressAssessmentView(assessment_id=run.id, sport=run.sport)
            for run in open_runs
        ]
