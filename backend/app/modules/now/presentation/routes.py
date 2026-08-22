"""``GET /api/v1/now`` — the whole screen, in one request.

The specification set writes ``GET /now``, which is a name for the screen rather
than an address; being the one route outside the version prefix is a cost that
buys nothing.

**The request carries the selected sport and nothing else.** No stamp of what the
phone is holding, no conditional header, and the server never answers *nothing
has changed* — Now is asked for only at moments where the player is explicitly
asking, and pull-to-refresh carries a promise a 304 would break.

**One request returns all three regions**, and the phone never learns that the
halves of the screen are cached on two different clocks.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.modules.now.application.commands import ComposeNowQuery, SportFilter
from app.modules.now.presentation.dependencies import ComposeNowDep
from app.modules.now.presentation.schemas import NowResponse
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/now", tags=["now"])


@router.get(
    "",
    response_model=NowResponse,
    status_code=status.HTTP_200_OK,
    summary="The Now screen: offers, your matches, and the shelves",
)
async def compose_now(
    current_user: CurrentUserDep,
    use_case: ComposeNowDep,
    sport: SportFilter = Query(
        default=SportFilter.ALL,
        description=(
            "The selected chip on the sport bar. `all` means the sports this "
            "player holds a rating at."
        ),
    ),
) -> NowResponse:
    screen = await use_case.execute(
        ComposeNowQuery(player_id=current_user.id, sport=sport)
    )
    return NowResponse.from_domain(screen)
