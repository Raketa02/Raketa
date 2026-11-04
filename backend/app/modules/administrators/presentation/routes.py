"""Invitations and the administrator profile, on the player surface
(``docs/adr/0184`` §2, §7; ``docs/adr/0185`` §6).

The administrator profile runs **under the player app's audience**: switching
profiles is client state, and the authority is not in the token — every
administrator operation names its club in its path and passes the guard on
every request.

Never under ``/api/v1/club``: anything beginning that way reads as the club
surface.
"""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.administrators.application.commands import (
    ClaimInvitationCommand,
    SetInvitationPasswordCommand,
)
from app.modules.administrators.presentation.dependencies import (
    AcceptInvitationDep,
    AdministratorAtClubDep,
    ClaimInvitationDep,
    ReadAccountProfilesDep,
    ReadAdministratorProfileDep,
    ReadInvitationByTokenDep,
    SetInvitationPasswordDep,
)
from app.modules.administrators.presentation.invitation_docs import (
    CREDENTIAL_REFUSALS,
    WEAK_PASSWORD,
)
from app.modules.administrators.presentation.schemas import (
    AccountProfilesSchema,
    AdministratorProfileResponse,
    ClaimInvitationRequest,
    InvitationByTokenRequest,
    InvitationByTokenResponse,
    InvitationPasswordRequest,
)
from app.modules.auth.presentation.schemas import ClaimTicketResponse, TokenResponse
from app.modules.users.presentation.dependencies import CurrentUserDep

invitations_router = APIRouter(prefix="/invitations", tags=["invitations"])
administrator_router = APIRouter(prefix="/administrator", tags=["administrator"])


@invitations_router.post(
    "/claim",
    response_model=ClaimTicketResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`code_incorrect` (`details.field`: `code`) — not the code sent "
                "to that address, **or nothing was sent to it**: one answer. "
                "Five wrong codes lock the invitation."
            ),
        },
        **CREDENTIAL_REFUSALS,
    },
    summary="Have an invitation code?: exchange it for a ticket",
    description=(
        "The email and the 8-character code from an invitation — or from the "
        "club's reset of an administrator. The ticket lasts a few minutes, "
        "and *Set your password* is set with it."
    ),
)
async def claim_invitation(
    payload: ClaimInvitationRequest, use_case: ClaimInvitationDep
) -> ClaimTicketResponse:
    ticket = await use_case.execute(
        ClaimInvitationCommand(email=payload.email, code=payload.code)
    )
    return ClaimTicketResponse.from_ticket(ticket)


@invitations_router.post(
    "/password",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **WEAK_PASSWORD,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "`credential_not_found` — a link or ticket never issued.",
        },
        **CREDENTIAL_REFUSALS,
    },
    summary="Set your password, by the invitation's link or a ticket, and sign in",
    description=(
        "**A new person's account is created** — no player name (the one the "
        "club typed stays the Administrator's), no nickname, and no Adult "
        "attestation — and **an account the "
        "club reset gets its password back**. Either way the administrator is "
        "active and this answers a signed-in session. `ticket_expired` is a "
        "409 too: claiming the code again is a fresh ticket."
    ),
)
async def set_invitation_password(
    payload: InvitationPasswordRequest, use_case: SetInvitationPasswordDep
) -> TokenResponse:
    pair = await use_case.execute(
        SetInvitationPasswordCommand(
            password=payload.password, token=payload.token, ticket=payload.ticket
        )
    )
    return TokenResponse.from_pair(pair)


@invitations_router.post(
    "/by-token",
    response_model=InvitationByTokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "`credential_not_found` — a link never issued.",
        },
    },
    summary="What an invitation's link opens",
    description=(
        "Read before anything is set: the email *Set your password* locks its "
        "field to, the name the club typed, the club, and whether the link "
        "still works. Changes nothing."
    ),
)
async def read_invitation_by_token(
    payload: InvitationByTokenRequest, use_case: ReadInvitationByTokenDep
) -> InvitationByTokenResponse:
    return InvitationByTokenResponse.from_opened(await use_case.execute(payload.token))


@invitations_router.post(
    "/{administrator_id}/acceptance",
    response_model=AccountProfilesSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`invitation_not_found` — no invitation to this account's email "
                "has that id: somebody else's, a removed one, or none."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "`invitation_expired` — ask the club to send a new one.",
        },
    },
    summary="Accept a pending invitation",
    description=(
        "For the signed-in account whose email the invitation names: the "
        "administrator profile is added, with no password step. Answers the "
        "account's profiles as `/users/me` would, so the switcher can be drawn "
        "at once. Accepting again is the same answer."
    ),
)
async def accept_invitation(
    administrator_id: UUID,
    user: CurrentUserDep,
    use_case: AcceptInvitationDep,
    profiles: ReadAccountProfilesDep,
) -> AccountProfilesSchema:
    await use_case.execute(
        account_id=user.id, email=user.email, administrator_id=administrator_id
    )
    return AccountProfilesSchema.from_profiles(
        await profiles.execute(account_id=user.id, email=user.email)
    )


@administrator_router.get(
    "/clubs/{club_id}",
    response_model=AdministratorProfileResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": (
                "`not_an_administrator` — this account holds no active "
                "administratorship at that club: removed since the last "
                "request, or never. **Every administrator operation answers "
                "this the same way.**"
            ),
        },
    },
    summary="My administrator profile at a club",
    description=(
        "The guarded read the administrator area opens on: the club's name. "
        "Checked for an active administratorship on every request."
    ),
)
async def administrator_profile(
    administratorship: AdministratorAtClubDep, use_case: ReadAdministratorProfileDep
) -> AdministratorProfileResponse:
    return AdministratorProfileResponse.from_profile(
        await use_case.execute(administratorship)
    )
