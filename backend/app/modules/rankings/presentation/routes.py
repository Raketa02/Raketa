"""The Rankings page's read (#768; ``docs/adr/0203`` §2–§5; the screens §2–§5).

**Read-only, and it tells nobody anything** (Q10): no push, bell line or email
is about a place.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.kernel import Sport
from app.modules.rankings.presentation.dependencies import ReadRankingDep
from app.modules.rankings.presentation.schemas import RankingResponse, RankingView
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get(
    "/{sport}",
    response_model=RankingResponse,
    status_code=status.HTTP_200_OK,
    summary="A sport's ranking",
    description=(
        "Your place card, the podium and the first page of the list, in one "
        "sport and view — sorted by the Level itself, competitive games only. "
        "An unknown sport is refused."
    ),
)
async def read_ranking(
    sport: Sport,
    user: CurrentUserDep,
    use_case: ReadRankingDep,
    view: RankingView = Query(
        default=RankingView.GENERAL,
        description="Which list: `GENERAL`, everybody in Raketa listed in the sport.",
    ),
) -> RankingResponse:
    return RankingResponse.of_ranking(await use_case.execute(user.id, sport), view=view)
