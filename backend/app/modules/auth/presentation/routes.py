from fastapi import APIRouter, Response, status

from app.modules.auth.application.forgot_password import (
    ClaimPasswordResetCommand,
    SetNewPasswordCommand,
)
from app.modules.auth.application.login import LoginCommand
from app.modules.auth.application.logout import LogoutCommand
from app.modules.auth.application.refresh_token import (
    RefreshTokensCommand,
)
from app.modules.auth.presentation.dependencies import (
    ClaimPasswordResetDep,
    LoginUseCaseDep,
    LogoutUseCaseDep,
    RefreshUseCaseDep,
    RequestPasswordResetDep,
    SetNewPasswordDep,
)
from app.modules.auth.presentation.forgot_password_docs import (
    CLAIM_RESPONSES,
    NEW_PASSWORD_RESPONSES,
    REQUEST_RESPONSES,
    claim_description,
    new_password_description,
    request_description,
)
from app.modules.auth.presentation.schemas import (
    ClaimCodeRequest,
    ClaimTicketResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    NewPasswordRequest,
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
    return TokenResponse.from_pair(pair)


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
    return TokenResponse.from_pair(pair)


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


# --- Forgot password? (docs/adr/0184 §5) ---------------------------------------


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    responses=REQUEST_RESPONSES,
    summary="Forgot password?: email a link and a code",
    description=request_description(
        "the public site's `/reset/<token>` page, for a player or an administrator"
    ),
)
async def forgot_password(
    payload: ForgotPasswordRequest, use_case: RequestPasswordResetDep
) -> Response:
    await use_case.execute(payload.email)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post(
    "/forgot-password/claim",
    response_model=ClaimTicketResponse,
    status_code=status.HTTP_200_OK,
    responses=CLAIM_RESPONSES,
    summary="Exchange the emailed code for a ticket",
    description=claim_description(),
)
async def claim_reset_code(
    payload: ClaimCodeRequest, use_case: ClaimPasswordResetDep
) -> ClaimTicketResponse:
    ticket = await use_case.execute(
        ClaimPasswordResetCommand(email=payload.email, code=payload.code)
    )
    return ClaimTicketResponse.from_ticket(ticket)


@router.post(
    "/forgot-password/new-password",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses=NEW_PASSWORD_RESPONSES,
    summary="Set a new password, sign out everywhere, and sign in",
    description=new_password_description("phone"),
)
async def set_new_password(
    payload: NewPasswordRequest, use_case: SetNewPasswordDep
) -> TokenResponse:
    pair = await use_case.execute(
        SetNewPasswordCommand(
            password=payload.password, token=payload.token, ticket=payload.ticket
        )
    )
    return TokenResponse.from_pair(pair)
