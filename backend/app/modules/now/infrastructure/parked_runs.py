"""``ParkedRuns`` over the rating context's own repository.

The one place in Now that knows a parked run is an ``Assessment`` with a stream
behind it. It takes the *port*, so the composition root decides what answers and
this file never learns that the rating context is event-sourced — the shape
``RatedSportsFromSkillRatings`` set beside it.

The read is **only made when a door is being drawn**, which is a named chip on a
sport the viewer holds no rating at. Every other compose — every ``all``, and
every chip she is rated at — never reaches this adapter at all.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Sport

from app.modules.now.domain.ports import ParkedRuns
from app.modules.rating.domain.ports import AssessmentRepository


class ParkedRunsFromAssessments(ParkedRuns):
    """Whether this player has an unfinished run at one sport."""

    def __init__(self, assessments: AssessmentRepository) -> None:
        self._assessments = assessments

    async def parked_at(self, *, player_id: UUID, sport: Sport) -> bool:
        open_run = await self._assessments.find_open(
            player_id=player_id, sport=sport
        )
        return open_run is not None
