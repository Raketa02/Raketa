"""The invitation page, on the public surface (``docs/adr/0187`` §4–§5).

A new person's invitation email has a button to the public site's
``/invite/<token>``. Opened on a phone without Raketa or on a laptop, that page
reads the link here — whom to greet, for which club, whether it still works,
and the code while it does — and can set the password right there.

Mounted under ``/api/v1/public``, and **no route here takes a session**.
Setting the password follows exactly the rules the app's *Set your password*
follows and leaves exactly its results, but **signs nobody in**: the site holds
no session, so the person then opens Raketa and signs in. The link's token is in
the body, never the path, so it is in no access log.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.exception_handlers import ErrorResponse
from app.modules.administrators.application.commands import (
    SetInvitationPasswordCommand,
)
from app.modules.administrators.presentation.dependencies import (
    ReadInvitationByTokenDep,
    SetInvitationPasswordWithoutSigningInDep,
)
from app.modules.administrators.presentation.invitation_docs import (
    CREDENTIAL_REFUSALS,
    WEAK_PASSWORD,
)
from app.modules.administrators.presentation.schemas import (
    InvitationByTokenRequest,
    InvitationPagePasswordRequest,
    InvitationPageResponse,
)

router = APIRouter(prefix="/invitations", tags=["public"])


@router.post(
    "/by-token",
    response_model=InvitationPageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`credential_not_found` — a link never issued as an invitation: "
                "a password reset's link included."
            ),
        },
    },
    summary="What an invitation's link opens, on the invitation page",
    description=(
        "Read before anything is set, whatever the link's state: the name to "
        "greet, the club, whether the link still works — and its code while "
        "it does. The club's reset of an administrator opens this page too. "
        "Changes nothing."
    ),
)
async def invitation_page(
    payload: InvitationByTokenRequest, use_case: ReadInvitationByTokenDep
) -> InvitationPageResponse:
    return InvitationPageResponse.from_opened(await use_case.execute(payload.token))


@router.post(
    "/password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        **WEAK_PASSWORD,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "`credential_not_found` — a link never issued.",
        },
        **CREDENTIAL_REFUSALS,
    },
    summary="Set your password here, by the invitation's link",
    description=(
        "**The same rules and the same results as the app's *Set your "
        "password***: a new person's account is created — no player name, no "
        "nickname, no Adult attestation — or an account the club "
        "reset gets its password back, and either way the administrator is "
        "active and the link is spent. **Nobody is signed in**: the page then "
        "says to open Raketa and sign in with this email and password."
    ),
)
async def set_password_on_the_invitation_page(
    payload: InvitationPagePasswordRequest,
    use_case: SetInvitationPasswordWithoutSigningInDep,
) -> Response:
    await use_case.execute(
        SetInvitationPasswordCommand(password=payload.password, token=payload.token)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
