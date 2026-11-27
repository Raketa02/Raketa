"""The Rankings page's reads (#768, #770, #771; ``docs/adr/0203`` §2–§5; the
screens §2–§5), and Home's Top 10, the top of the same list (#797;
``docs/adr/0204`` §8).

**Read-only, and it tells nobody anything** (Q10): no push, bell line or email
is about a place.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.core.exception_handlers import ErrorResponse
from app.kernel import Sport
from app.modules.rankings.domain.errors import NotAPage, NotOneSport
from app.modules.rankings.domain.ranking import RankingView
from app.modules.rankings.presentation.dependencies import (
    ReadGeneralPageDep,
    ReadRankingDep,
    ReadTopTenDep,
)
from app.modules.rankings.presentation.schemas import (
    GeneralPageResponse,
    RankingResponse,
    TopTenResponse,
    key_of,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/rankings", tags=["rankings"])
top_ten_router = APIRouter(prefix="/top-10", tags=["rankings"])


@router.get(
    "/{sport}",
    response_model=RankingResponse,
    status_code=status.HTTP_200_OK,
    summary="A sport's ranking",
    description=(
        "Your place card, the podium and the list, in one sport and view — "
        "sorted by the Level itself, competitive games only: General's first "
        "page, or the whole of Friends. An unknown sport is refused.\n\n"
        "**The real ranking** (`docs/adr/0204` §2): everybody is listed at "
        "their true place, a player you blocked or who blocked you included, "
        "and *of N* counts everyone. Their record stays closed to you."
    ),
)
async def read_ranking(
    sport: Sport,
    user: CurrentUserDep,
    use_case: ReadRankingDep,
    view: RankingView = Query(
        default=RankingView.GENERAL,
        description=(
            "Which list: `GENERAL`, everybody in Rakieta listed in the sport; "
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


@top_ten_router.get(
    "",
    response_model=TopTenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`not_one_sport` — neither `sport` nor `prefer`, or both at once."
            ),
        },
    },
    summary="Home's Top 10 row",
    description=(
        "The first ten rows of General in one sport — the true top of the "
        "Rankings page, everybody at their true place, whoever blocked whom. "
        "Name the sport **exactly** with `sport` (the pill), or **prefer** one "
        "with `prefer` (the trophy's sport, on opening): with nobody listed in "
        "it, the row shows the next sport in the app's order where somebody "
        "is, going round from the last to the first. One of the two, never "
        "both. `anyone_listed` says whether the row shows at all."
    ),
)
async def read_top_ten(
    user: CurrentUserDep,
    use_case: ReadTopTenDep,
    sport: Sport | None = Query(
        default=None,
        description="This sport exactly — empty when nobody is listed in it.",
    ),
    prefer: Sport | None = Query(
        default=None,
        description=(
            "This sport, or, with nobody listed in it, the next in the app's "
            "order where somebody is."
        ),
    ),
) -> TopTenResponse:
    if sport is not None and prefer is None:
        top = await use_case.execute(user.id, sport)
    elif prefer is not None and sport is None:
        top = await use_case.execute(user.id, prefer, falls_through=True)
    else:
        raise NotOneSport()
    return TopTenResponse.of_top_ten(top)
