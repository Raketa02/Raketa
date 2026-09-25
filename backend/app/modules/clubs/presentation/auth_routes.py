"""The club's session: sign in, refresh, sign out — **for the club audience**.

The same three acts as the player's ``/auth`` routes, with the same shapes and
the same refusals, built for the other audience (``docs/adr/0185`` §6): a pair
issued here is refused on the player surface, and a player's pair is refused
here. Sign-out is idempotent and says nothing about a token it does not
recognise, including one the player app issued.
"""

from fastapi import APIRouter, status

from app.modules.auth.application.logout import LogoutCommand
from app.modules.auth.application.refresh_token import RefreshTokensCommand
from app.modules.auth.presentation.schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    TokenResponse,
)
from app.modules.clubs.application.commands import SignInClubCommand
from app.modules.clubs.presentation.dependencies import (
    RefreshClubTokensDep,
    SignInClubDep,
    SignOutClubDep,
)

router = APIRouter(prefix="/auth", tags=["club-auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign the club in and obtain a club access/refresh token pair",
    description=(
        "Club accounts only: a player's email and password are refused with "
        "`invalid_credentials`, exactly as a stranger's are."
    ),
)
async def sign_in(payload: LoginRequest, use_case: SignInClubDep) -> TokenResponse:
    pair = await use_case.execute(
        SignInClubCommand(email=payload.email, password=payload.password)
    )
    return TokenResponse.from_pair(pair)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate the club's access and refresh tokens",
)
async def refresh(
    payload: RefreshRequest, use_case: RefreshClubTokensDep
) -> TokenResponse:
    pair = await use_case.execute(
        RefreshTokensCommand(presented_token=payload.refresh_token)
    )
    return TokenResponse.from_pair(pair)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign the club out: revoke its refresh token (idempotent)",
)
async def sign_out(payload: LogoutRequest, use_case: SignOutClubDep) -> LogoutResponse:
    await use_case.execute(LogoutCommand(presented_token=payload.refresh_token))
    return LogoutResponse()
