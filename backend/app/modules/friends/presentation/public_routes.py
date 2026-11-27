"""A Friend link's owner, on the public surface (``docs/adr/0187`` §4–§5;
#748).

Mounted under ``/api/v1/public``, which only the public site consumes, and **no
route here takes a session**: the page ``/f/<code>`` opens is for somebody who
has not installed the app — *Tomek invited you to play on Rakieta*. It answers
the owner's nickname and face, **and nothing else about them**.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.friends.presentation.dependencies import ReadAFriendLinkDep
from app.modules.friends.presentation.schemas import LinkedFriendResponse

router = APIRouter(prefix="/friend-links", tags=["public"])


@router.get(
    "/{code}",
    response_model=LinkedFriendResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`friend_link_not_found` — *Nothing at that link*: the code was "
                "replaced by a New link, no link ever carried it, or it could be "
                "no link's."
            ),
        },
    },
    summary="Who a friend link is from",
    description=(
        "`code` is what follows `/f/` in the link, read in any case. The owner's "
        "nickname and first photograph — **and nothing else about them**."
    ),
)
async def friend_link_page(code: str, read: ReadAFriendLinkDep) -> LinkedFriendResponse:
    return LinkedFriendResponse.of(await read.execute(code))
