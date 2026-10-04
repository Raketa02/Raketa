"""A group by its link, on the public surface (``docs/adr/0187`` §4–§5).

Mounted under ``/api/v1/public``, which only the public site consumes, and
**no route here takes a session**: the page a group link opens is for somebody
who has not installed the app, let alone signed in. It answers the least that
page needs and never who is in the group.

The code is in the path, and deliberately so: unlike an invitation's token it
is no secret — it is the link a WhatsApp group was sent.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.groups.presentation.dependencies import ReadGroupByLinkDep
from app.modules.groups.presentation.schemas import LinkedGroupResponse

router = APIRouter(prefix="/groups", tags=["public"])


@router.get(
    "/{code}",
    response_model=LinkedGroupResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`group_not_found` — a link that leads nowhere: no group has "
                "that code, it could be no group's, or its group was deleted."
            ),
        },
    },
    summary="The group a link opens",
    description=(
        "`code` is what follows `/join/` in the group's link, read in any case. "
        "Its name, monogram, club and district, sport dots and member count — "
        "**and never who is in it**."
    ),
)
async def group_by_link(code: str, read: ReadGroupByLinkDep) -> LinkedGroupResponse:
    return LinkedGroupResponse.from_view(await read.execute(code))
