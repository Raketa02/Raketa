"""The friend routes: ask, answer, take back, read your own, and ask a friend
for a level (``docs/adr/0202`` §1–§2, §4; the mechanics §3, §5).

**Silent but for three things**: a request is told to the person asked, once,
*you're friends* to whoever asked, and an ask for a level to the friend asked —
who, once their level arrives, has it told back to the asker. *Not now*, a
cancel and a removal tell nobody, and **a removal touches no game**.

**Every response carries only your own relations** — nothing here names
anybody's friend but yours, and nothing tells you whether somebody set your
request aside or blocked you: both read *request sent*, for as long as it stays
open.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.exception_handlers import ErrorResponse
from app.kernel import Sport
from app.modules.friends.application.commands import (
    AnswerCommand,
    AskCommand,
    AskForALevelCommand,
    TakeBackCommand,
)
from app.modules.friends.application.reads import Direction
from app.modules.friends.presentation.dependencies import (
    AcceptFriendRequestDep,
    AskForALevelDep,
    AskToBeFriendsDep,
    CancelFriendRequestDep,
    ReadFriendRequestsDep,
    ReadFriendsDep,
    ReadGroupsToAddFromDep,
    RemoveFriendDep,
    SetAsideFriendRequestDep,
)
from app.modules.friends.presentation.schemas import (
    AskForALevelRequest,
    AskToBeFriendsRequest,
    FriendRequestSchema,
    FriendRequestsResponse,
    FriendSchema,
    FriendsResponse,
    GroupsToAddFromResponse,
    GroupToAddFromSchema,
    RelationResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/friends", tags=["friends"])

_NO_REQUEST: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`friend_request_not_found` — no request from them is waiting for "
            "you: never made, cancelled, answered or ended."
        ),
    },
}


@router.post(
    "/requests",
    response_model=RelationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "`cannot_befriend_yourself` — you named yourself.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`player_not_in_your_groups` — they are in none of your groups. "
                "Somebody outside them can be asked only through your link."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`already_friends`; `friend_request_already_sent` — your request "
                "to them is still open, set aside or not, and nobody asks twice; "
                "`unblock_them_first` — you blocked them; "
                "`concurrent_modification` — two acts on the two of you raced: "
                "retry."
            ),
        },
    },
    summary="Ask to be friends",
    description=(
        "**+ Add** on Members or the result's *PLAYED WITH* card, **Add friend** "
        "on the record. Their Home gets a card naming the group you asked from "
        "while you are both in it, and they are told once.\n\n"
        "**If they had already asked you, the requests cross**: you are friends "
        "at once, both are told, and the answer is `FRIEND`.\n\n"
        "**Otherwise `SENT`, for as long as the request is open.** Nothing ever "
        "tells you whether they set it aside: *request sent* is all you read, and "
        "a request never expires. Cancel it with `DELETE /friends/requests/"
        "{player_id}`."
    ),
)
async def ask_to_be_friends(
    payload: AskToBeFriendsRequest, user: CurrentUserDep, use_case: AskToBeFriendsDep
) -> RelationResponse:
    relation = await use_case.execute(
        AskCommand(
            requester_id=user.id, addressee_id=payload.player_id, where=payload.where()
        )
    )
    return RelationResponse(relation=relation)


@router.post(
    "/requests/{player_id}/acceptance",
    response_model=RelationResponse,
    status_code=status.HTTP_200_OK,
    responses=_NO_REQUEST,
    summary="Accept a friend request",
    description=(
        "**Accept** — on their Home card, their Members row, their record or "
        "*Asked you* — also after **Not now**. You are friends at once, and they "
        "are told *… said yes — you're friends*."
    ),
)
async def accept_friend_request(
    player_id: UUID, user: CurrentUserDep, use_case: AcceptFriendRequestDep
) -> RelationResponse:
    relation = await use_case.execute(
        AnswerCommand(reader_id=user.id, requester_id=player_id)
    )
    return RelationResponse(relation=relation)


@router.post(
    "/requests/{player_id}/set-aside",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Set aside — also when it already was."
        },
        **_NO_REQUEST,
    },
    summary="Not now",
    description=(
        "**Not now is not no.** The card leaves your Home and its notice leaves "
        "your bell; the request stays open, **Accept** still answers it, and "
        "they are never told — they keep reading *request sent* and cannot ask "
        "again."
    ),
)
async def set_aside_friend_request(
    player_id: UUID, user: CurrentUserDep, use_case: SetAsideFriendRequestDep
) -> None:
    await use_case.execute(AnswerCommand(reader_id=user.id, requester_id=player_id))


@router.delete(
    "/requests/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "Your request to them is cancelled — also the answer when none "
                "was open."
            )
        },
    },
    summary="Cancel your friend request",
    description=(
        "**Request sent ▾ › Cancel request**, or *You asked*'s **Cancel**. It "
        "leaves their Home and their bell, and **nobody is told**."
    ),
)
async def cancel_friend_request(
    player_id: UUID, user: CurrentUserDep, use_case: CancelFriendRequestDep
) -> None:
    await use_case.execute(TakeBackCommand(player_id=user.id, other_id=player_id))


@router.delete(
    "/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "You are no longer friends — also the answer when you were not."
            )
        },
    },
    summary="Remove a friend",
    description=(
        "**Friend ✓ ▾ › Remove friend**, behind its confirmation. **Nobody is "
        "told, and no game is touched**: a game already sent or booked with them "
        "stays as it is."
    ),
)
async def remove_friend(
    player_id: UUID, user: CurrentUserDep, use_case: RemoveFriendDep
) -> None:
    await use_case.execute(TakeBackCommand(player_id=user.id, other_id=player_id))


@router.get(
    "",
    response_model=FriendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Your friends",
    description=(
        "Every friend you have, from all your groups, each with every sport "
        "they are rated in — their Level and its band. With `sport`, each "
        "carries that sport alone (empty where they have no Level in it), "
        "highest Level first: the picker's list."
    ),
)
async def read_friends(
    user: CurrentUserDep,
    use_case: ReadFriendsDep,
    sport: Sport | None = Query(
        default=None, description="Narrow every friend's sports to this one."
    ),
) -> FriendsResponse:
    friends = await use_case.execute(user.id, sport=sport)
    return FriendsResponse(
        sport=sport, friends=[FriendSchema.of(friend) for friend in friends]
    )


@router.get(
    "/requests",
    response_model=FriendRequestsResponse,
    status_code=status.HTTP_200_OK,
    summary="Asked you · You asked",
    description=(
        "Open requests in one direction, newest first: `ASKED_YOU` — made of "
        "you, **Accept** on each; `YOU_ASKED` — yours, **Cancel** on each."
    ),
)
async def read_friend_requests(
    user: CurrentUserDep,
    use_case: ReadFriendRequestsDep,
    direction: Direction = Query(description="Which tab."),
) -> FriendRequestsResponse:
    requests = await use_case.execute(user.id, direction=direction)
    return FriendRequestsResponse(
        direction=direction,
        requests=[FriendRequestSchema.of(request) for request in requests],
    )


@router.get(
    "/groups",
    response_model=GroupsToAddFromResponse,
    status_code=status.HTTP_200_OK,
    summary="Add friends — from your groups",
    description=(
        "Each of your groups with how many people are in it and how many of "
        "them you could still ask — *8 members · 2 to add*. Tapping one opens "
        "its Members."
    ),
)
async def read_groups_to_add_from(
    user: CurrentUserDep, use_case: ReadGroupsToAddFromDep
) -> GroupsToAddFromResponse:
    groups = await use_case.execute(user.id)
    return GroupsToAddFromResponse(
        groups=[GroupToAddFromSchema.of(group) for group in groups]
    )


@router.post(
    "/{player_id}/level-asks",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "Asked: they are told, and your picker reads **Asked** "
                "(`level_asked_in`)."
            )
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`friend_not_found` — they are not your friend (or you named "
                "yourself); `not_one_of_your_groups` — `group_id` is no group "
                "you are in."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`already_has_a_level` — they have a level in that sport: seat "
                "them; `level_already_asked` — you asked them for that sport "
                "before, and ask once per sport, ever; "
                "`concurrent_modification` — two acts on the two of you raced: "
                "retry."
            ),
        },
    },
    summary="Ask a friend to get a level",
    description=(
        "**Ask {nickname} to get a padel level**, on a greyed row of a group's "
        "picker (#749). They are told, pushed and in the bell: *{you} wants to "
        "play padel with you. Get your padel level so {you} can add you.* — "
        "`LEVEL_ASKED`, opening that sport's questionnaire.\n\n"
        "**When their first level in the sport arrives, you are told**: "
        "*{nickname} has a padel level — you can seat {nickname} now.* — "
        "`LEVEL_GOT`, opening this group's picker. Both only while you are "
        "still friends."
    ),
)
async def ask_for_a_level(
    player_id: UUID,
    payload: AskForALevelRequest,
    user: CurrentUserDep,
    use_case: AskForALevelDep,
) -> None:
    await use_case.execute(
        AskForALevelCommand(
            asker_id=user.id,
            friend_id=player_id,
            sport=payload.sport,
            group_id=payload.group_id,
        )
    )
