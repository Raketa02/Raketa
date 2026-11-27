"""The Friend link on the player surface: read yours, take a New link, and open
somebody's (``docs/adr/0202`` §1; the mechanics §4; #748).

**Opening a link never makes friends by itself**: it puts the owner's request on
your Home, *Invited you to Rakieta*, to accept or set aside like any request. The
code is in the path, as a group's is: it is the link a chat was sent, and no
secret.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, status

from app.api.dependencies import SettingsDep
from app.core.exception_handlers import ErrorResponse
from app.modules.friends.application.link import OpenLinkCommand
from app.modules.friends.presentation.dependencies import (
    OpenAFriendLinkDep,
    ReadYourFriendLinkDep,
    ReplaceYourFriendLinkDep,
)
from app.modules.friends.presentation.schemas import (
    FriendLinkResponse,
    OpenedFriendLinkResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/friends", tags=["friends"])

_RACED: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`concurrent_modification` — two reads or New links of yours raced: retry."
        ),
    },
}


@router.get(
    "/link",
    response_model=FriendLinkResponse,
    status_code=status.HTTP_200_OK,
    responses=_RACED,
    summary="Your friend link",
    description=(
        "The Add friends sheet's *Not on Rakieta yet?* card: `<public site>/f/"
        "<code>`, **made the first time you read it** and the same on every read "
        "after, until you take a New link. Somebody who opens it finds your "
        "request on their Home."
    ),
)
async def read_your_friend_link(
    user: CurrentUserDep, use_case: ReadYourFriendLinkDep, settings: SettingsDep
) -> FriendLinkResponse:
    code = await use_case.execute(user.id)
    return FriendLinkResponse.of(code, public_site=settings.PUBLIC_SITE_URL)


@router.post(
    "/link/replacement",
    response_model=FriendLinkResponse,
    status_code=status.HTTP_200_OK,
    responses=_RACED,
    summary="New link",
    description=(
        "A fresh code, and **the old one dead at once**: opened in the app or on "
        "the public site, it reads `friend_link_not_found`. Requests already made "
        "through it stay as they are. No code is ever handed out twice."
    ),
)
async def replace_your_friend_link(
    user: CurrentUserDep, use_case: ReplaceYourFriendLinkDep, settings: SettingsDep
) -> FriendLinkResponse:
    code = await use_case.execute(user.id)
    return FriendLinkResponse.of(code, public_site=settings.PUBLIC_SITE_URL)


@router.post(
    "/links/{code}/opening",
    response_model=OpenedFriendLinkResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`friend_link_not_found` — *Nothing at that link*: the code was "
                "replaced by a New link, or no link ever carried it."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`unblock_them_first` — you blocked the link's owner; "
                "`concurrent_modification` — two acts on the two of you raced: "
                "retry."
            ),
        },
    },
    summary="Open a friend link",
    description=(
        "`code` is what follows `/f/` in the link, read in any case. **The "
        "owner's request lands on your Home**, *{nickname} wants to be your "
        "friend · Invited you to Rakieta*, with Accept and Not now — whether or "
        "not you share a group. Opened again, it makes no second request, and a "
        "request of theirs you set aside comes back to Home.\n\n"
        "**Nothing happens** for your own link (`NONE`) or a friend's "
        "(`FRIEND`). **If you had asked them, the requests cross**: you are "
        "friends at once (`FRIEND`)."
    ),
)
async def open_a_friend_link(
    code: str, user: CurrentUserDep, use_case: OpenAFriendLinkDep
) -> OpenedFriendLinkResponse:
    relation = await use_case.execute(OpenLinkCommand(opener_id=user.id, code=code))
    return OpenedFriendLinkResponse(relation=relation)
