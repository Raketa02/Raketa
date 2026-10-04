"""The club's official groups, on the club surface (#510, ``docs/adr/0183`` §8,
§11).

Mounted under ``/api/v1/club``, which only the club website consumes
(``docs/adr/0187`` §5), and every route takes a **club-audience** token: a club
reads its own official groups, hands them between its own Administrators, and
answers the Join requests waiting on them (``docs/adr/0191`` §1).

**There is no route that creates one**: official groups are made by the club's
Administrators, in the app (``docs/adr/0183`` §3).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.clubs.presentation.dependencies import CurrentClubAccountDep
from app.modules.groups.application.commands import (
    AnswerAsClubCommand,
    HandOverCommand,
)
from app.modules.groups.presentation.dependencies import (
    ApproveAsClubDep,
    DeclineAsClubDep,
    HandOverOfficialGroupDep,
    ReadClubGroupRequestsDep,
    ReadClubGroupsDep,
)
from app.modules.groups.presentation.schemas import (
    ClubGroupSchema,
    ClubGroupsResponse,
    ClubJoinRequestSchema,
    ClubJoinRequestsResponse,
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


_NOT_THE_CLUB_S = (
    "`group_not_found` — not an official group of this club: no such group, a "
    "player group whose home club this is, or another club's."
)


@router.get(
    "/{group_id}/requests",
    response_model=ClubJoinRequestsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": _NOT_THE_CLUB_S,
        },
    },
    summary="The Join requests waiting on one of the club's official groups",
    description=(
        "*Want to join · N*: everybody waiting, **in the order they asked** — "
        "whoever runs the group, and **while it needs an administrator**, when "
        "the club is the only one who can answer. Each is a name and every "
        "sport they are rated in with its Level."
    ),
)
async def club_group_requests(
    group_id: UUID,
    account: CurrentClubAccountDep,
    read: ReadClubGroupRequestsDep,
) -> ClubJoinRequestsResponse:
    cards = await read.execute(group_id, club_id=account.club_id)
    return ClubJoinRequestsResponse(
        requests=[ClubJoinRequestSchema.from_card(card) for card in cards]
    )


@router.post(
    "/{group_id}/requests/{player_id}/approve",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                f"{_NOT_THE_CLUB_S} `join_request_not_found` — the player has no "
                "request waiting: whoever runs the group answered it first, it "
                "was declined, or it was never made, and nobody is admitted who "
                "did not ask. Nothing was recorded."
            ),
        },
    },
    summary="Approve a Join request on one of the club's official groups",
    description=(
        "The player is a Group member **at once**, as if whoever runs the group "
        "had said yes — who runs it does not change. Approving somebody already "
        "in changes nothing."
    ),
)
async def approve_club_group_request(
    group_id: UUID,
    player_id: UUID,
    account: CurrentClubAccountDep,
    approve: ApproveAsClubDep,
) -> None:
    await approve.execute(
        AnswerAsClubCommand(
            club_id=account.club_id,
            answered_by=account.id,
            group_id=group_id,
            player_id=player_id,
        )
    )


@router.post(
    "/{group_id}/requests/{player_id}/decline",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": f"{_NOT_THE_CLUB_S} Nothing was recorded.",
        },
    },
    summary="Decline a Join request on one of the club's official groups",
    description=(
        "The request is gone **silently**: nothing tells the player, and they "
        "may ask again. Declining a request that is not waiting changes "
        "nothing, and never removes a member."
    ),
)
async def decline_club_group_request(
    group_id: UUID,
    player_id: UUID,
    account: CurrentClubAccountDep,
    decline: DeclineAsClubDep,
) -> None:
    await decline.execute(
        AnswerAsClubCommand(
            club_id=account.club_id,
            answered_by=account.id,
            group_id=group_id,
            player_id=player_id,
        )
    )
