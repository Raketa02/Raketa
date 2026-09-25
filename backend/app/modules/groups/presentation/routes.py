"""The player surface's group routes: create one, list yours, open one, join
one or ask to, answer the requests waiting on yours, see who in it plays a
sport, edit yours, leave one or delete yours — and the two searches, for a home
club and for a group to join.

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
from app.kernel import Sport
from app.modules.groups.application.commands import (
    AnswerJoinRequestCommand,
    CreatePlayerGroupCommand,
    DeleteGroupCommand,
    EditGroupCommand,
    JoinGroupCommand,
    LeaveGroupCommand,
    SearchGroupsToJoinCommand,
    SearchHomeClubsCommand,
)
from app.modules.groups.presentation.dependencies import (
    ApproveJoinRequestDep,
    CreatePlayerGroupDep,
    DeclineJoinRequestDep,
    DeleteGroupDep,
    EditGroupDep,
    JoinGroupDep,
    LeaveGroupDep,
    ReadGroupDep,
    ReadGroupMembersDep,
    ReadJoinRequestsDep,
    ReadMyGroupsDep,
    SearchGroupsToJoinDep,
    SearchHomeClubsDep,
)
from app.modules.groups.presentation.schemas import (
    CreatePlayerGroupRequest,
    EditedGroupResponse,
    EditGroupRequest,
    GroupAtClubSchema,
    GroupMemberSchema,
    GroupMembersResponse,
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

#: A read that leaves a blocked pair out reads the block state first, and a
#: block state that cannot be read is not guessed at (``docs/adr/0095`` §5).
#: A reader alone in the group has nobody to hide, and is never refused this.
_BLOCKS_UNREAD: dict[int | str, dict[str, Any]] = {
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": (
            "`block_state_unavailable` — who is blocked could not be read, and "
            "faces nobody could check are not served. Nothing was recorded; "
            "retry."
        ),
    },
}

_OWNER_ONLY: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`not_the_group_owner` — the caller is in the group and is not its "
            "Owner. **Nobody but the Owner** sees or answers its requests, edits "
            "it or deletes it."
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
    responses={**_NOT_FOUND, **_BLOCKS_UNREAD},
    summary="A group, for its members",
    description=(
        "Its name, monogram, dots, member count and home club; its link and "
        "join policy; whether the caller owns it; for every sport, how many "
        "members are rated in it and the first of them to join — the Games "
        "tab's *N of M*; and the faces on the Info tab's members row, which "
        "**leaves out a blocked pair, either way round**, as the Members list "
        "does. No count moves."
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


@router.put(
    "/{group_id}/details",
    response_model=EditedGroupResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={
        **_OWNER_ONLY,
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`group_name_invalid` (`details.field` `name`) — 1–40 characters "
                "once trimmed. Read only once the caller is known to be the "
                "Owner. **Nothing was recorded** — the policy neither."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`group_not_found` — no such group, or one the caller is not in."
            ),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": (
                "`block_state_unavailable` — who is blocked could not be read "
                "for the answer's members row. **Nothing was recorded**: the "
                "answer is drawn before the save commits, so the retry is the "
                "whole edit again."
            ),
        },
    },
    summary="Edit a group: its name and who can join",
    description=(
        "**The Owner's**, both fields as *Edit group* holds them, recorded "
        "together or not at all. Saving what the group already says records "
        "nothing. **The link never changes**, and nor does the monogram's "
        "colour. **Switching to `ANYONE` admits everybody waiting at once**, "
        "and `admitted` says who. Answers the group as its page reads it, "
        "under `group`."
    ),
)
async def edit_group(
    group_id: UUID,
    payload: EditGroupRequest,
    user: CurrentUserDep,
    edit: EditGroupDep,
    settings: SettingsDep,
) -> EditedGroupResponse:
    edited = await edit.execute(
        EditGroupCommand(
            group_id=group_id,
            editor_id=user.id,
            name=payload.name,
            join_policy=payload.join_policy,
        )
    )
    return EditedGroupResponse.from_view(edited, public_site=settings.PUBLIC_SITE_URL)


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        **_OWNER_ONLY,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`group_not_found` — no such group, or one the caller is not in."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`group_has_other_members` — somebody besides the Owner is in it. "
                "A group is deleted only while its Owner is its only member; an "
                "Owner who wants out of one with people in it leaves. Nothing "
                "was recorded."
            ),
        },
    },
    summary="Delete a group nobody else is in",
    description=(
        "**The Owner, and only while they are its only member.** Afterwards the "
        "group is in no list and no search, its link reads *nothing at that "
        "link* (join search answers `read_as` `LINK` and no clubs), and the "
        "requests waiting on it are gone."
    ),
)
async def delete_group(
    group_id: UUID, user: CurrentUserDep, delete: DeleteGroupDep
) -> None:
    await delete.execute(DeleteGroupCommand(group_id=group_id, deleted_by=user.id))


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


@router.delete(
    "/{group_id}/membership",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`group_not_found` — no such group, or one the caller is not in: "
                "a second tap on *Leave* meets this, because they are not in it "
                "any more."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`lone_owner_cannot_leave` — the caller owns the group and is its "
                "only member, so there is nobody to pass it to. *Delete the "
                "group* is what undoes it. Nothing was recorded."
            ),
        },
    },
    summary="Leave a group",
    description=(
        "The caller is no longer a member, and may join again later under the "
        "group's policy. **An Owner leaving a group other people are in passes "
        "it to the member who has been in longest** — their current stay, so "
        "somebody who left and came back counts from their return — and the "
        "requests waiting on it pass with it."
    ),
)
async def leave_group(
    group_id: UUID, user: CurrentUserDep, leave: LeaveGroupDep
) -> None:
    await leave.execute(LeaveGroupCommand(group_id=group_id, player_id=user.id))


@router.get(
    "/{group_id}/members",
    response_model=GroupMembersResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={**_NOT_FOUND, **_BLOCKS_UNREAD},
    summary="Members of a group, for one sport",
    description=(
        "**Only the members rated in `sport`** — who in the group the caller "
        "could play it with: the caller first, then the Owner, then everybody "
        "else newest joined first. Each with their face, their Level in the "
        "sport, their Player Score where they have one, whether they own the "
        "group and when they joined. **A blocked pair, either way round, is "
        "left out of each other's list**, and the group's member count does "
        "not change."
    ),
)
async def group_members(
    group_id: UUID,
    user: CurrentUserDep,
    read: ReadGroupMembersDep,
    sport: Sport = Query(description="The sport whose players to list."),
) -> GroupMembersResponse:
    rows = await read.execute(group_id, reader_id=user.id, sport=sport)
    return GroupMembersResponse(
        sport=sport, members=[GroupMemberSchema.from_row(row) for row in rows]
    )


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
