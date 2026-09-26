"""The club's official groups, on the club surface (#510, ``docs/adr/0183`` §8,
§11).

Mounted under ``/api/v1/club``, which only the club website consumes
(``docs/adr/0187`` §5), and every route takes a **club-audience** token: a club
reads its own official groups and hands them between its own Administrators.

**There is no route that creates one**: official groups are made by the club's
Administrators, in the app (``docs/adr/0183`` §3).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.clubs.presentation.dependencies import CurrentClubAccountDep
from app.modules.groups.application.commands import HandOverCommand
from app.modules.groups.presentation.dependencies import (
    HandOverOfficialGroupDep,
    ReadClubGroupsDep,
)
from app.modules.groups.presentation.schemas import (
    ClubGroupSchema,
    ClubGroupsResponse,
    HandOverRequest,
)

router = APIRouter(prefix="/groups", tags=["club"])


@router.get(
    "",
    response_model=ClubGroupsResponse,
    status_code=status.HTTP_200_OK,
    summary="The club's official groups, and how much of each WhatsApp crowd arrived",
    description=(
        "*Official groups at [club]*: each one's name and monogram, who runs it "
        "— or `null`, *needs an administrator* — its players and how many are "
        "waiting, *From WhatsApp* as players of the WhatsApp group's size, and "
        "how many games it gave birth to. By name."
    ),
)
async def club_groups(
    account: CurrentClubAccountDep, read: ReadClubGroupsDep
) -> ClubGroupsResponse:
    rows = await read.execute(account.club_id)
    return ClubGroupsResponse(groups=[ClubGroupSchema.from_view(row) for row in rows])


@router.put(
    "/{group_id}/administrator",
    response_model=ClubGroupSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`group_not_found` — not an official group of this club: no such "
                "group, a player group whose home club this is, or another "
                "club's. Nothing was recorded."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`administrator_not_active` — the one chosen is not an active "
                "Administrator of this club: still invited, expired, removed, "
                "another club's, or nobody. Nothing was recorded; choose again "
                "from the Administrators table as it stands."
            ),
        },
    },
    summary="Hand an official group over to one of the club's administrators",
    description=(
        "Any official group of the club, **one that needs an administrator "
        "included**, to any **active** Administrator. Only who answers "
        "changes: the link, who can join, the WhatsApp size, the players and "
        "**the requests waiting** all stay, and the new Administrator finds "
        "them. The previous one stops seeing it — and stays in it if they "
        "joined it as a player. Handing it to whoever runs it changes nothing. "
        "Answers the group's row as the table now reads it."
    ),
)
async def hand_over(
    group_id: UUID,
    payload: HandOverRequest,
    account: CurrentClubAccountDep,
    use_case: HandOverOfficialGroupDep,
) -> ClubGroupSchema:
    row = await use_case.execute(
        HandOverCommand(
            club_id=account.club_id,
            assigned_by=account.id,
            group_id=group_id,
            administrator_id=payload.administrator_id,
        )
    )
    return ClubGroupSchema.from_view(row)
