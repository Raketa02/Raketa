"""The club's Administrators page, on the club surface (``docs/adr/0184``).

Mounted under ``/api/v1/club``, which only the club website consumes
(``docs/adr/0187`` §5), and every route takes a **club-audience** token: the
club acts on its own Administrators and on nobody else's.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Response, status

from app.core.exception_handlers import ErrorResponse
from app.modules.administrators.application.commands import (
    InviteAdministratorCommand,
)
from app.modules.administrators.presentation.dependencies import (
    InviteAdministratorDep,
    ListClubAdministratorsDep,
    RemoveAdministratorDep,
    ResendInvitationDep,
    ResetAdministratorPasswordDep,
)
from app.modules.administrators.presentation.schemas import (
    AdministratorListResponse,
    AdministratorSchema,
    InviteAdministratorRequest,
)
from app.modules.clubs.presentation.dependencies import CurrentClubAccountDep

router = APIRouter(prefix="/administrators", tags=["club"])

_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`administrator_not_found` — no administrator of this club has that "
            "id: another club's, a removed one, or none."
        ),
    },
}


@router.get(
    "",
    response_model=AdministratorListResponse,
    status_code=status.HTTP_200_OK,
    summary="The club's administrators, and where each one stands",
)
async def list_administrators(
    account: CurrentClubAccountDep, use_case: ListClubAdministratorsDep
) -> AdministratorListResponse:
    rows = await use_case.execute(account.club_id)
    return AdministratorListResponse(
        administrators=[AdministratorSchema.from_row(row) for row in rows]
    )


@router.post(
    "",
    response_model=AdministratorSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "A field the desk has to correct, named by `details.field`: "
                "`administrator_name_invalid` or `email_invalid`. Nothing was "
                "recorded and nothing was sent."
            ),
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`administrator_already_invited` — that email is invited here, "
                "expired included: resend instead — or "
                "`administrator_already_active`. `details.field` is `email`."
            ),
        },
    },
    summary="Invite an administrator by name and email",
    description=(
        "Emails the person through the mail queue, in this request's "
        "transaction. **A new person** gets a button to the public site's "
        "`/invite/<token>` and an 8-character code, valid 72 hours; **an "
        'existing account** gets *"[Club] wants to make you an '
        'administrator"* and a button that opens the app, with no code. '
        "Inviting somebody this club removed invites them again."
    ),
)
async def invite_administrator(
    payload: InviteAdministratorRequest,
    account: CurrentClubAccountDep,
    use_case: InviteAdministratorDep,
) -> AdministratorSchema:
    row = await use_case.execute(
        InviteAdministratorCommand(
            club_id=account.club_id, name=payload.name, email=payload.email
        )
    )
    return AdministratorSchema.from_row(row)


@router.post(
    "/{administrator_id}/invitation",
    response_model=AdministratorSchema,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`administrator_already_active` — there is nothing left to open."
            ),
        },
    },
    summary="Resend an invitation: a fresh 72 hours",
    description=(
        "For somebody `INVITED` or `EXPIRED`. The email is the original's "
        "again, with a new link and code where it carries them; the older "
        "ones stop working."
    ),
)
async def resend_invitation(
    administrator_id: UUID,
    account: CurrentClubAccountDep,
    use_case: ResendInvitationDep,
) -> AdministratorSchema:
    row = await use_case.execute(
        club_id=account.club_id, administrator_id=administrator_id
    )
    return AdministratorSchema.from_row(row)


@router.post(
    "/{administrator_id}/password-reset",
    response_model=AdministratorSchema,
    status_code=status.HTTP_200_OK,
    responses={
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`administrator_also_plays` — the account also plays, and only "
                "its owner resets it, through *Forgot password?*; or "
                "`administrator_has_no_account` — nobody has set a password "
                "yet: resend instead. Nothing moved."
            ),
        },
    },
    summary="Reset an administrator's password",
    description=(
        "**Only for an account that holds nothing but administrator "
        "profiles** — `can_reset_password` on the row. Clears the password, "
        "signs the account out everywhere, and puts the person back to "
        "`INVITED` with a fresh 72-hour email carrying the invitation's own "
        "link and code."
    ),
)
async def reset_administrator_password(
    administrator_id: UUID,
    account: CurrentClubAccountDep,
    use_case: ResetAdministratorPasswordDep,
) -> AdministratorSchema:
    row = await use_case.execute(
        club_id=account.club_id, administrator_id=administrator_id
    )
    return AdministratorSchema.from_row(row)


@router.delete(
    "/{administrator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_NOT_FOUND,
    summary="Remove an administrator",
    description=(
        "The administrator profile ends: the person's next administrator "
        "request is refused with `not_an_administrator`. Their player profile "
        "and their sessions are untouched, and an invitation still in their "
        "inbox opens nothing."
    ),
)
async def remove_administrator(
    administrator_id: UUID,
    account: CurrentClubAccountDep,
    use_case: RemoveAdministratorDep,
) -> Response:
    await use_case.execute(club_id=account.club_id, administrator_id=administrator_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
