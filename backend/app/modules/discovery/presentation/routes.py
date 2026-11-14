"""Home's people rows (#793; ``docs/adr/0204`` §5, §10, §12; the home-rows
mechanics §7). **New in Raketa** is here; Same competitive level and Same vibe
join it (#794, #795).

**Read-only, and it tells nobody anything** (the mechanics §14): no push, bell
line or email is about somebody joining Raketa. A request sent from a tile is an
ordinary friend request, `made_from` `NEW_PLAYERS`.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, status

from app.core.exception_handlers import ErrorResponse
from app.kernel import Sport
from app.modules.discovery.presentation.dependencies import (
    ReadNewInRaketaPageDep,
    ReadNewInRaketaDep,
)
from app.modules.discovery.presentation.schemas import (
    NewInRaketaPlayerSchema,
    NewInRaketaPageResponse,
    NewInRaketaResponse,
    key_of,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

new_in_raketa_router = APIRouter(prefix="/new-in-raketa", tags=["discovery"])

_LEFT_OUT = (
    "**Never on it**: you, anybody you blocked or who blocked you, players with "
    "*Show me to new people* off, and accounts that don't play."
)

_BLOCKS_UNREADABLE: dict[int | str, dict[str, Any]] = {
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": (
            "`block_state_unavailable` — the blocks couldn't be read, so no "
            "row is shown rather than one that might suggest a blocked person."
        ),
    },
}


@new_in_raketa_router.get(
    "",
    response_model=NewInRaketaResponse,
    status_code=status.HTTP_200_OK,
    responses=_BLOCKS_UNREADABLE,
    summary="Home's New in Raketa row",
    description=(
        "The players who finished sign-up in the **last 30 days**, strictly — "
        "the 10 newest, unrated ones included — those you aren't connected "
        "with first, then those you sent a request to, then your friends, "
        "newest first within each. An 11th sign-up pushes the oldest off the "
        "row; they stay in See all until their 30 days end. " + _LEFT_OUT
    ),
)
async def read_new_in_raketa(
    user: CurrentUserDep, use_case: ReadNewInRaketaDep
) -> NewInRaketaResponse:
    return NewInRaketaResponse(
        players=[
            NewInRaketaPlayerSchema.of(card) for card in await use_case.execute(user.id)
        ]
    )


@new_in_raketa_router.get(
    "/all",
    response_model=NewInRaketaPageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`not_a_new_in_raketa_page` — a cursor this server never wrote."
            ),
        },
        **_BLOCKS_UNREADABLE,
    },
    summary="New in Raketa's See all",
    description=(
        "Every player who joined in the last 30 days, newest first, friends where they "
        "fall, in pages of 20 — with `sport`, only those holding a level in "
        "it — and the sports at least one of them holds a level in. " + _LEFT_OUT
    ),
)
async def read_new_in_raketa_page(
    user: CurrentUserDep,
    use_case: ReadNewInRaketaPageDep,
    sport: Sport | None = Query(
        default=None,
        description="Keep only the players holding a level in this sport.",
    ),
    after: str | None = Query(
        default=None,
        description="A `next` cursor: the 20 players behind it.",
    ),
) -> NewInRaketaPageResponse:
    return NewInRaketaPageResponse.of(
        await use_case.execute(
            user.id, sport=sport, after=None if after is None else key_of(after)
        )
    )
