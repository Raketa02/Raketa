"""The player surface's group routes: create one, list yours, open one, join
one — and search for a home club.

Mounted on the player surface (``app/api/v1/player.py``). Every route takes a
player's token. **The backend guards no flag** (``docs/adr/0183`` §12): these
answer whatever ``find_a_game`` says, because nothing behind them is dangerous
to call.

**Home-club search is ``/home-clubs`` and never ``/clubs``**: everything under
``/api/v1/club`` is the club website's surface, and a player path that merely
began with those letters would read as one of its paths (``docs/adr/0187`` §5).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.dependencies import SettingsDep
from app.core.exception_handlers import ErrorResponse
from app.modules.groups.application.commands import (
    CreatePlayerGroupCommand,
    JoinGroupCommand,
    SearchHomeClubsCommand,
)
from app.modules.groups.presentation.dependencies import (
    CreatePlayerGroupDep,
    JoinGroupDep,
    ReadGroupDep,
    ReadMyGroupsDep,
    SearchHomeClubsDep,
)
from app.modules.groups.presentation.schemas import (
    CreatePlayerGroupRequest,
    GroupAtClubSchema,
    GroupResponse,
    HomeClubPageResponse,
    MyGroupSchema,
    MyGroupsResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/groups", tags=["groups"])
home_clubs_router = APIRouter(prefix="/home-clubs", tags=["groups"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`group_not_found` — **one code for two cases**: no such group, and "
            "a group the reader is not a member of. Both have one remedy."
        ),
    },
}


@router.post(
    "",
    response_model=GroupResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "A field the player has to correct, named by `details.field`, "
                "checked in the form's order: `group_name_invalid` (`name`) — "
                "1–40 characters once trimmed; `home_club_unknown` "
                "(`home_club_id`) — only a club in Raketa can be a home club. "
                "Nothing was recorded."
            ),
        },
    },
    summary="Create a player group at a home club",
    description=(
        "The caller becomes the group's **Owner and first member**, and the "
        "group gets its link, which never changes. Answers the group as its "
        "page reads it."
    ),
)
async def create_group(
    payload: CreatePlayerGroupRequest,
    user: CurrentUserDep,
    create: CreatePlayerGroupDep,
    read: ReadGroupDep,
    settings: SettingsDep,
) -> GroupResponse:
    group_id = await create.execute(
        CreatePlayerGroupCommand(
            creator_id=user.id,
            name=payload.name,
            home_club_id=payload.home_club_id,
            join_policy=payload.join_policy,
        )
    )
    page = await read.execute(group_id, reader_id=user.id)
    return GroupResponse.from_view(page, public_site=settings.PUBLIC_SITE_URL)


@router.get(
    "",
    response_model=MyGroupsResponse,
    status_code=status.HTTP_200_OK,
    summary="The groups the caller belongs to, newest joined first",
)
async def my_groups(user: CurrentUserDep, read: ReadMyGroupsDep) -> MyGroupsResponse:
    groups = await read.execute(user.id)
    return MyGroupsResponse(groups=[MyGroupSchema.from_view(group) for group in groups])


@router.get(
    "/{group_id}",
    response_model=GroupResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses=_NOT_FOUND,
    summary="A group, for its members",
    description=(
        "Its name, monogram, dots, member count and home club; its link and "
        "join policy; whether the caller owns it; and, for every sport, how "
        "many members are rated in it and the first of them to join — the "
        "Games tab's *N of M*."
    ),
)
async def read_group(
    group_id: UUID,
    user: CurrentUserDep,
    read: ReadGroupDep,
    settings: SettingsDep,
) -> GroupResponse:
    page = await read.execute(group_id, reader_id=user.id)
    return GroupResponse.from_view(page, public_site=settings.PUBLIC_SITE_URL)


@router.post(
    "/{group_id}/membership",
    response_model=GroupAtClubSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "`group_not_found` — there is no such group.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`group_needs_approval` — the group admits people its Owner "
                "approves, and a tap cannot admit anybody to it. Nothing was "
                "recorded."
            ),
        },
    },
    summary="Join a group",
    description=(
        "Under *Anyone* the caller is a member **at once**. Joining a group "
        "you are already in changes nothing and answers the same. Answers the "
        "group as a club's card draws it, with the caller's relation."
    ),
)
async def join_group(
    group_id: UUID, user: CurrentUserDep, join: JoinGroupDep
) -> GroupAtClubSchema:
    joined = await join.execute(JoinGroupCommand(group_id=group_id, player_id=user.id))
    return GroupAtClubSchema.from_view(joined)


@home_clubs_router.get(
    "",
    response_model=HomeClubPageResponse,
    status_code=status.HTTP_200_OK,
    summary="Search every club in Raketa for a group's home club",
    description=(
        "Clubs whose name or district contains `q` anywhere, ignoring case and "
        "accents (*debniki* finds *Dębniki*). **Nearest first** from the "
        "caller's Location area, then by name, twenty to a page; a caller with "
        "no Location area gets A–Z and no distance. A blank `q` finds nothing. "
        "Each club carries every group at it and what each is to the caller."
    ),
)
async def search_home_clubs(
    user: CurrentUserDep,
    search: SearchHomeClubsDep,
    q: str = Query(description="What was typed into the home club field."),
    page: int = Query(1, ge=1, description="Which page, from one."),
) -> HomeClubPageResponse:
    results = await search.execute(
        SearchHomeClubsCommand(reader_id=user.id, text=q, page=page)
    )
    return HomeClubPageResponse.from_view(results)
