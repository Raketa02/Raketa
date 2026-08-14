"""Find the assessments a player has in progress — for one sport, or for all.

This is what makes resume survive a force-quit, a reinstall and a new handset:
nothing about the transcript ever lived on the device, so the client asks the
server whether a run is already open. No device cache and no parallel index is
involved — the repository finds the streams themselves, and each sport is fully
isolated, so a query for one sport can never surface another's.

Two shapes, because the client asks the question two ways. Resuming a sport it
has already chosen is a question about that sport. The entry gate's question —
*is any run unfinished* — is about the player, and asking it one sport at a time
cost four requests on every cold launch for an answer that is almost always
"no". Both are the repository's finders, so the two cannot answer differently.
"""

from __future__ import annotations

from app.engines.assessment import AssessmentEngine
from app.modules.rating.application.assessment_view import current_step
from app.modules.rating.application.commands import (
    AssessmentStep,
    FindInProgressQuery,
    InProgressAssessmentView,
    ListInProgressQuery,
)
from app.modules.rating.domain.ports import AssessmentRepository


class FindInProgressAssessment:
    def __init__(
        self,
        *,
        engine: AssessmentEngine,
        assessments: AssessmentRepository,
    ) -> None:
        self._engine = engine
        self._assessments = assessments

    async def execute(self, query: FindInProgressQuery) -> AssessmentStep | None:
        assessment = await self._assessments.find_open(
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

    def __init__(self, *, assessments: AssessmentRepository) -> None:
        self._assessments = assessments

    async def execute(
        self, query: ListInProgressQuery
    ) -> list[InProgressAssessmentView]:
        open_runs = await self._assessments.find_all_open(player_id=query.player_id)
        return [
            InProgressAssessmentView(assessment_id=run.id, sport=run.sport)
            for run in open_runs
        ]
