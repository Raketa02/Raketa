from fastapi import APIRouter, status

from app.modules.auth.application.login import LoginCommand
from app.modules.auth.application.logout import LogoutCommand
from app.modules.auth.application.refresh_token import (
    RefreshTokensCommand,
)
from app.modules.auth.presentation.dependencies import (
    LoginUseCaseDep,
    LogoutUseCaseDep,
    RefreshUseCaseDep,
)
from app.modules.auth.presentation.schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and obtain an access/refresh token pair",
)
async def login(
    payload: LoginRequest,
    use_case: LoginUseCaseDep,
) -> TokenResponse:
    pair = await use_case.execute(
        LoginCommand(email=payload.email, password=payload.password)
    )
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
        expires_in=pair.expires_in,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate access and refresh tokens",
)
async def refresh(
    payload: RefreshRequest,
    use_case: RefreshUseCaseDep,
) -> TokenResponse:
    pair = await use_case.execute(
        RefreshTokensCommand(presented_token=payload.refresh_token)
    )
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
        expires_in=pair.expires_in,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a refresh token (idempotent)",
)
async def logout(
    payload: LogoutRequest,
    use_case: LogoutUseCaseDep,
) -> LogoutResponse:
    await use_case.execute(LogoutCommand(presented_token=payload.refresh_token))
    return LogoutResponse()
