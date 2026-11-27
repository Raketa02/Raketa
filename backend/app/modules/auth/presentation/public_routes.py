"""The reset page, on the public surface (``docs/adr/0187`` §4–§5).

*Forgot password?* in the app emails a button to the public site's
``/reset/<token>``, for a player or an administrator. Opened on a phone without
Rakieta or on a laptop, that page reads here whether the link still works, and
sets the new password.

Mounted under ``/api/v1/public``, and **no route here takes a session**.
Setting the password follows exactly the rules of the app's *Forgot password?*
and leaves exactly its results — every phone signed out — but **signs nobody
in**: the site holds no session. A club's link opens the club website's own
page, and is ``credential_not_found`` here. The token is in the body, never the
path, so it is in no access log.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.exception_handlers import ErrorResponse
from app.modules.auth.application.forgot_password import SetNewPasswordCommand
from app.modules.auth.presentation.dependencies import (
    ReadPasswordResetByTokenDep,
    SetNewPasswordWithoutSigningInDep,
)
from app.modules.auth.presentation.forgot_password_docs import (
    NEW_PASSWORD_RESPONSES,
)
from app.modules.auth.presentation.schemas import (
    ResetPagePasswordRequest,
    ResetPageRequest,
    ResetPageResponse,
)

router = APIRouter(prefix="/password-resets", tags=["public"])

_NOT_A_RESET = (
    "`credential_not_found` — a link never issued as a player's or an "
    "administrator's reset: a club's, or an invitation's, included."
)


@router.post(
    "/by-token",
    response_model=ResetPageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": _NOT_A_RESET,
        },
    },
    summary="Whether a reset's link still works",
    description=(
        "Read before anything is set, whatever the link's state — its state and "
        "nothing else. Changes nothing."
    ),
)
async def reset_page(
    payload: ResetPageRequest, use_case: ReadPasswordResetByTokenDep
) -> ResetPageResponse:
    return ResetPageResponse.from_standing(await use_case.execute(payload.token))


@router.post(
    "/password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: NEW_PASSWORD_RESPONSES[
            status.HTTP_400_BAD_REQUEST
        ],
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": _NOT_A_RESET,
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "`credential_expired` (ask again), `credential_used` or "
                "`credential_locked` (five wrong codes)."
            ),
        },
    },
    summary="Set a new password by a reset's link, and sign out everywhere",
    description=(
        "**The same rules and the same results as the app's *Forgot "
        "password?***: the password rule, the link spent, and **every session "
        "signed out** — every access token issued before this moment is "
        "refused (`access_token_revoked`) and every refresh token revoked. "
        "**Nobody is signed in**: the page then says to open Rakieta and sign in "
        "with the new password."
    ),
)
async def set_password_on_the_reset_page(
    payload: ResetPagePasswordRequest, use_case: SetNewPasswordWithoutSigningInDep
) -> Response:
    await use_case.execute(
        SetNewPasswordCommand(password=payload.password, token=payload.token)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
