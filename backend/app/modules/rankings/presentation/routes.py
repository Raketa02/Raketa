"""The Rankings page's reads (#768, #770, #771; ``docs/adr/0203`` §2–§5; the
screens §2–§5).

**Read-only, and it tells nobody anything** (Q10): no push, bell line or email
is about a place.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.core.exception_handlers import ErrorResponse
from app.kernel import Sport
from app.modules.rankings.domain.errors import NotAPage
from app.modules.rankings.domain.ranking import RankingView
from app.modules.rankings.presentation.dependencies import (
    ReadGeneralPageDep,
    ReadRankingDep,
)
from app.modules.rankings.presentation.schemas import (
    GeneralPageResponse,
    RankingResponse,
    key_of,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/rankings", tags=["rankings"])

#: A block is read live on every read (#772), and a read that cannot read the
#: blocks fails rather than show a blocked pair each other's rows.
_BLOCKS_UNREADABLE = {
    "model": ErrorResponse,
    "description": (
        "`block_state_unavailable` — your blocks could not be read, so no list "
        "is drawn. Retry the same request."
    ),
}


@router.get(
    "/{sport}",
    response_model=RankingResponse,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: _BLOCKS_UNREADABLE},
    summary="A sport's ranking",
    description=(
        "Your place card, the podium and the list, in one sport and view — "
        "sorted by the Level itself, competitive games only: General's first "
        "page, or the whole of Friends. An unknown sport is refused."
    ),
)
async def read_ranking(
    sport: Sport,
    user: CurrentUserDep,
    use_case: ReadRankingDep,
    view: RankingView = Query(
        default=RankingView.GENERAL,
        description=(
            "Which list: `GENERAL`, everybody in Raketa listed in the sport; "
            "`FRIENDS`, you and your friends, from the first result."
        ),
    ),
) -> RankingResponse:
    return RankingResponse.of_ranking(await use_case.execute(user.id, sport, view=view))


@router.get(
    "/{sport}/general/rows",
    response_model=GeneralPageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`not_a_ranking_page` — a cursor this server never wrote, or a "
                "page asked for in two places at once."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: _BLOCKS_UNREADABLE,
    },
    summary="A page of a sport's General list",
    description=(
        "General in pages of 50, best first: **after** a cursor, **before** "
        "one, or **around you** — the 50 rows with you in the middle, held to "
        "the list's ends. With none of them it is the first page, the main "
        "read's own; around you when you aren't listed is the first page too. "
        "Each page carries the cursors for the page above and below. A row "
        "that moved since the last page is never shown twice for the rows it "
        "passed."
    ),
)
async def read_general_page(
    sport: Sport,
    user: CurrentUserDep,
    use_case: ReadGeneralPageDep,
    after: str | None = Query(
        default=None,
        description="A `next` cursor: the 50 rows below it.",
    ),
    before: str | None = Query(
        default=None,
        description="A `previous` cursor: the 50 rows above it.",
    ),
    around_me: bool = Query(
        default=False,
        description="The page with your row in the middle — *You · 212th*.",
    ),
) -> GeneralPageResponse:
    if sum((after is not None, before is not None, around_me)) > 1:
        raise NotAPage("after, before and around me are one each")
    return GeneralPageResponse.of_page(
        await use_case.execute(
            user.id,
            sport,
            after=None if after is None else key_of(after),
            before=None if before is None else key_of(before),
            around_the_reader=around_me,
        )
    )
