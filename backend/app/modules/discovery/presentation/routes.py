"""Home's people rows (#793, #794, #795; ``docs/adr/0204`` §4–§6, §10, §12;
the home-rows mechanics §6–§8). **New in Raketa**, **Same competitive level**
and **Same vibe** are here.

**Read-only, and they tell nobody anything** (the mechanics §14): no push, bell
line or email is about somebody joining Raketa, reading as even or sharing a
tag. A request sent from a card is an ordinary friend request, `made_from`
`NEW_PLAYERS`, `SAME_LEVEL` or `SAME_VIBE`.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, status

from app.core.exception_handlers import ErrorResponse
from app.kernel import Sport
from app.modules.discovery.presentation.dependencies import (
    ReadNewInRaketaPageDep,
    ReadNewInRaketaDep,
    ReadSameLevelDep,
    ReadSameLevelPageDep,
    ReadSameVibeDep,
    ReadSameVibePageDep,
)
from app.modules.discovery.presentation.schemas import (
    NewInRaketaPlayerSchema,
    NewInRaketaPageResponse,
    NewInRaketaResponse,
    SameLevelPageResponse,
    SameLevelPlayerSchema,
    SameLevelResponse,
    SameVibePageResponse,
    SameVibePlayerSchema,
    SameVibeResponse,
    key_of,
    same_level_key_of,
    same_vibe_key_of,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

new_in_raketa_router = APIRouter(prefix="/new-in-raketa", tags=["discovery"])
same_level_router = APIRouter(prefix="/same-level", tags=["discovery"])
same_vibe_router = APIRouter(prefix="/same-vibe", tags=["discovery"])

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


@same_level_router.get(
    "",
    response_model=SameLevelResponse,
    status_code=status.HTTP_200_OK,
    responses=_BLOCKS_UNREADABLE,
    summary="Home's Same competitive level players row",
    description=(
        "The players a competitive game with would be most even — each in the "
        "sport where you two are evenest, by the app's Forecast with one player "
        "a side. Ten: fresh good matches first (70% or more, not your friend, "
        "not asked by you; somebody who asked you counts as fresh), then the "
        "gaps — friends, those you asked, weaker matches — best % first. "
        "**Empty while you hold no level anywhere.** " + _LEFT_OUT
    ),
)
async def read_same_level(
    user: CurrentUserDep, use_case: ReadSameLevelDep
) -> SameLevelResponse:
    return SameLevelResponse(
        players=[
            SameLevelPlayerSchema.of(card) for card in await use_case.execute(user.id)
        ]
    )


@same_level_router.get(
    "/all",
    response_model=SameLevelPageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`not_a_same_level_page` — a cursor this server never wrote."
            ),
        },
        **_BLOCKS_UNREADABLE,
    },
    summary="Same competitive level's See all",
    description=(
        "Everybody who shares a sport with you, best % first, friends where "
        "they fall, in pages of 20 — each in your evenest shared sport, or with "
        "`sport` everybody holding a level in it, compared there — and the "
        "sports you share with somebody. Empty while you hold no level. " + _LEFT_OUT
    ),
)
async def read_same_level_page(
    user: CurrentUserDep,
    use_case: ReadSameLevelPageDep,
    sport: Sport | None = Query(
        default=None,
        description="Compare everybody in this sport, and keep only them.",
    ),
    after: str | None = Query(
        default=None,
        description="A `next` cursor: the 20 players behind it.",
    ),
) -> SameLevelPageResponse:
    return SameLevelPageResponse.of(
        await use_case.execute(
            user.id,
            sport=sport,
            after=None if after is None else same_level_key_of(after),
        )
    )


@same_vibe_router.get(
    "",
    response_model=SameVibeResponse,
    status_code=status.HTTP_200_OK,
    responses=_BLOCKS_UNREADABLE,
    summary="Home's Same vibe players row",
    description=(
        "The players whose Social tags overlap yours, most in common first — "
        "ties to fewer of their tags you don't hold, then the player id — each "
        "with the vibe %, 1 − ½ⁿ for n shared tags. Every tag counts the same, "
        "and skill plays no part, so a player with no level sees it too. Ten: "
        "fresh good matches first (2 shared tags or more, not your friend, not "
        "asked by you; somebody who asked you counts as fresh), then the gaps "
        "— friends, those you asked, 1-tag matches — in the same order. " + _LEFT_OUT
    ),
)
async def read_same_vibe(
    user: CurrentUserDep, use_case: ReadSameVibeDep
) -> SameVibeResponse:
    return SameVibeResponse(
        players=[
            SameVibePlayerSchema.of(card) for card in await use_case.execute(user.id)
        ]
    )


@same_vibe_router.get(
    "/all",
    response_model=SameVibePageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`not_a_same_vibe_page` — a cursor this server never wrote."
            ),
        },
        **_BLOCKS_UNREADABLE,
    },
    summary="Same vibe's See all",
    description=(
        "Everybody who shares a Social tag with you, most in common first, "
        "friends where they fall, in pages of 20 — with `sport`, only those "
        "holding a level in it — and the sports at least one of them holds a "
        "level in. " + _LEFT_OUT
    ),
)
async def read_same_vibe_page(
    user: CurrentUserDep,
    use_case: ReadSameVibePageDep,
    sport: Sport | None = Query(
        default=None,
        description="Keep only the players holding a level in this sport.",
    ),
    after: str | None = Query(
        default=None,
        description="A `next` cursor: the 20 players behind it.",
    ),
) -> SameVibePageResponse:
    return SameVibePageResponse.of(
        await use_case.execute(
            user.id,
            sport=sport,
            after=None if after is None else same_vibe_key_of(after),
        )
    )
