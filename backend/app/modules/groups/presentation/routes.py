"""The player surface's group routes: create one, list yours, open one, join
one or ask to, answer the requests waiting on yours — and the two searches, for a
home club and for a group to join.

Mounted on the player surface (``app/api/v1/player.py``). Every route takes a
player's token. **The backend guards no flag** (``docs/adr/0183`` §12): these
answer whatever ``find_a_game`` says, because nothing behind them is dangerous
to call.

**Home-club search is ``/home-clubs`` and never ``/clubs``**: everything under
``/api/v1/club`` is the club website's surface, and a player path that merely
began with those letters would read as one of its paths (``docs/adr/0187`` §5).
**Join search is ``/join-search``** and not ``/groups/search``, which the path
``/groups/{group_id}`` would read as a group id.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.dependencies import SettingsDep
from app.core.exception_handlers import ErrorResponse
from app.modules.groups.application.commands import (
    AnswerJoinRequestCommand,
    CreatePlayerGroupCommand,
    JoinGroupCommand,
    SearchGroupsToJoinCommand,
    SearchHomeClubsCommand,
)
from app.modules.groups.presentation.dependencies import (
    ApproveJoinRequestDep,
    CreatePlayerGroupDep,
    DeclineJoinRequestDep,
    JoinGroupDep,
    ReadGroupDep,
    ReadJoinRequestsDep,
    ReadMyGroupsDep,
    SearchGroupsToJoinDep,
    SearchHomeClubsDep,
)
from app.modules.groups.presentation.schemas import (
    CreatePlayerGroupRequest,
    GroupAtClubSchema,
    GroupResponse,
    HomeClubPageResponse,
    JoinRequestSchema,
    JoinRequestsResponse,
    JoinSearchResponse,
    MyGroupSchema,
    MyGroupsResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/groups", tags=["groups"])
home_clubs_router = APIRouter(prefix="/home-clubs", tags=["groups"])
join_search_router = APIRouter(prefix="/join-search", tags=["groups"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`group_not_found` — **one code for two cases**: no such group, and "
            "a group the reader is not a member of. Both have one remedy."
        ),
    },
}

_OWNER_ONLY: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`not_the_group_owner` — the caller is in the group and is not its "
            "Owner. **Nobody but the Owner** sees or answers its requests."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`group_not_found` — no such group, or one the caller is not in: the "
            "person waiting is not in it yet, and meets this too."
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
    },
    summary="Join a group, or ask to",
    description=(
        "**One tap, and the group's policy decides what it was.** Under "
        "*Anyone* the caller is a member **at once** (`relation` `MEMBER`). "
        "Under *People I approve* their Join request waits for the Owner "
        "(`relation` `REQUESTED`). Neither is recorded twice: tapping again as "
        "a member, or while the request waits, changes nothing and answers the "
        "same. Answers the group as a club's card draws it, so the card is "
        "patched in place."
    ),
)
async def join_group(
    group_id: UUID, user: CurrentUserDep, join: JoinGroupDep
) -> GroupAtClubSchema:
    joined = await join.execute(JoinGroupCommand(group_id=group_id, player_id=user.id))
    return GroupAtClubSchema.from_view(joined)


@router.get(
    "/{group_id}/requests",
    response_model=JoinRequestsResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses=_OWNER_ONLY,
    summary="The Join requests waiting on a group, for its Owner",
    description=(
        "*Want to join · N*: everybody waiting, in the order they asked — each "
        "with their name, their face and every sport they are rated in with its "
        "Level."
    ),
)
async def join_requests(
    group_id: UUID, user: CurrentUserDep, read: ReadJoinRequestsDep
) -> JoinRequestsResponse:
    cards = await read.execute(group_id, reader_id=user.id)
    return JoinRequestsResponse(
        requests=[JoinRequestSchema.from_card(card) for card in cards]
    )


@router.post(
    "/{group_id}/requests/{player_id}/approve",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        **_OWNER_ONLY,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`group_not_found` — no such group, or one the caller is not "
                "in. `join_request_not_found` — the player has no request "
                "waiting: it was declined, or never made, and nobody is admitted "
                "who did not ask. Nothing was recorded."
            ),
        },
    },
    summary="Approve a Join request",
    description=(
        "The player is a Group member **at once**. Approving somebody already "
        "in changes nothing."
    ),
)
async def approve_join_request(
    group_id: UUID,
    player_id: UUID,
    user: CurrentUserDep,
    approve: ApproveJoinRequestDep,
) -> None:
    await approve.execute(
        AnswerJoinRequestCommand(
            group_id=group_id, player_id=player_id, answered_by=user.id
        )
    )


@router.post(
    "/{group_id}/requests/{player_id}/decline",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_OWNER_ONLY,
    summary="Decline a Join request",
    description=(
        "The request is gone **silently**: nothing tells the player, their "
        "relation to the group is `NONE` again, and they may ask again. "
        "Declining a request that is not waiting changes nothing, and never "
        "removes a member."
    ),
)
async def decline_join_request(
    group_id: UUID,
    player_id: UUID,
    user: CurrentUserDep,
    decline: DeclineJoinRequestDep,
) -> None:
    await decline.execute(
        AnswerJoinRequestCommand(
            group_id=group_id, player_id=player_id, answered_by=user.id
        )
    )


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


@join_search_router.get(
    "",
    response_model=JoinSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for a group to join by club, district, group name or link",
    description=(
        "One field, four matches, answered as **club cards with groups "
        "inside**. A club whose name or district contains `q` comes with "
        "**every** group at it; a group whose name contains `q` comes inside its "
        "club's card, with **only** the matching groups when the club itself "
        "did not match — ignoring case and accents either way. **Any text "
        "containing `/join/<code>` is a link**, whatever domain or words are "
        "around it, and finds exactly that group; a link that leads nowhere "
        "answers no clubs with `read_as` `LINK` — *nothing at that link*. "
        "**Nearest first** from the caller's Location area, then by name, twenty "
        "to a page; a caller with no Location area gets A–Z and no distance. A "
        "blank `q` finds nothing."
    ),
)
async def join_search(
    user: CurrentUserDep,
    search: SearchGroupsToJoinDep,
    q: str = Query(description="What was typed or pasted into *Join a group*."),
    page: int = Query(1, ge=1, description="Which page, from one."),
) -> JoinSearchResponse:
    results = await search.execute(
        SearchGroupsToJoinCommand(reader_id=user.id, text=q, page=page)
    )
    return JoinSearchResponse.from_view(results)
