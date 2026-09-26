"""The club surface's own routes: signing up, and the club's details.

Mounted only on the club surface (``app/api/v1/club.py``), which only the club
website consumes (``docs/adr/0187`` §5). Every route but the sign-up takes a
**club-audience** token; a player's is refused.
"""

from typing import Any

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.clubs.application.commands import (
    ChangeClubDetailsCommand,
    SignUpClubCommand,
)
from app.modules.clubs.presentation.dependencies import (
    ChangeClubDetailsDep,
    CurrentClubAccountDep,
    ReadClubDetailsDep,
    SignUpClubDep,
)
from app.modules.clubs.presentation.schemas import (
    ClubDetailsRequest,
    ClubDetailsResponse,
    ClubSignUpRequest,
)

router = APIRouter(tags=["club"])

_FIELD_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "A field the desk has to correct, named by `details.field`: "
            "`club_name_invalid`, `club_district_invalid`, `club_city_invalid`, "
            "`club_sports_required` or `club_point_invalid`. Nothing was "
            "recorded. The website writes the sentence under that field."
        ),
    },
}


@router.post(
    "/sign-up",
    response_model=ClubDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "A field the desk has to correct, named by `details.field` — "
                "the five details' codes, and `email_invalid` or "
                "`password_too_weak`. Every field is checked before the email "
                "is looked up."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`club_email_already_registered` — another club's account signs "
                "in with this email; `details.field` is `email`. A player "
                "holding the same address is never a conflict."
            ),
        },
    },
    summary="Sign a club up, with the account its desk signs in with",
    description=(
        "Creates the club and its account **together, in one transaction**. "
        "There is no verification step. The account then signs in at "
        "`POST /api/v1/club/auth/login` — this route issues no tokens."
    ),
)
async def sign_up(
    payload: ClubSignUpRequest, use_case: SignUpClubDep
) -> ClubDetailsResponse:
    club = await use_case.execute(
        SignUpClubCommand(
            details=payload.to_input(),
            email=payload.email,
            password=payload.password,
        )
    )
    return ClubDetailsResponse.from_domain(club)


@router.get(
    "/details",
    response_model=ClubDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="The signed-in club's details",
)
async def read_details(
    account: CurrentClubAccountDep, use_case: ReadClubDetailsDep
) -> ClubDetailsResponse:
    return ClubDetailsResponse.from_domain(await use_case.execute(account.club_id))


@router.put(
    "/details",
    response_model=ClubDetailsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **_FIELD_REFUSALS,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`club_sport_declared_by_group` — the save unticks a sport an "
                "official group at the club declares; `details.field` is "
                "`sports`, `details.sport` the sport and `details.group` the "
                "group's name (the first by name, where several play it). "
                "Nothing was recorded. The group's administrator changes its "
                "sports first, or the sport stays ticked."
            ),
        },
    },
    summary="Change the signed-in club's details",
    description=(
        "A full replacement of the five details, at any time. Saving them "
        "unchanged records nothing. **A sport an official group declares cannot "
        "be unticked**, and the refusal names the group. Answers the details as "
        "recorded — names trimmed and collapsed, sports in the registry's order."
    ),
)
async def change_details(
    payload: ClubDetailsRequest,
    account: CurrentClubAccountDep,
    use_case: ChangeClubDetailsDep,
) -> ClubDetailsResponse:
    club = await use_case.execute(
        ChangeClubDetailsCommand(club_id=account.club_id, details=payload.to_input())
    )
    return ClubDetailsResponse.from_domain(club)
