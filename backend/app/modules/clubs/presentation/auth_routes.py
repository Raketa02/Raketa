"""The club's session: sign in, refresh, sign out, and *Forgot password?* —
**for the club audience**.

The same acts as the player's ``/auth`` routes, with the same shapes and the
same refusals, built for the other audience (``docs/adr/0185`` §6): a pair
issued here is refused on the player surface, and a player's pair is refused
here. Sign-out is idempotent and says nothing about a token it does not
recognise, including one the player app issued. A reset link or code the player
app's *Forgot password?* sent opens nothing here, even for an email both
identities share.
"""

from fastapi import APIRouter, Response, status

from app.modules.auth.application.forgot_password import (
    ClaimPasswordResetCommand,
    SetNewPasswordCommand,
)
from app.modules.auth.application.logout import LogoutCommand
from app.modules.auth.application.refresh_token import RefreshTokensCommand
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
from app.modules.clubs.application.commands import SignInClubCommand
from app.modules.clubs.presentation.dependencies import (
    ClaimClubPasswordResetDep,
    RefreshClubTokensDep,
    RequestClubPasswordResetDep,
    SetNewClubPasswordDep,
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


# --- Forgot password? (docs/adr/0184 §5) ---------------------------------------


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    responses=REQUEST_RESPONSES,
    summary="Forgot password?: email the club a link and a code",
    description=request_description(
        "the club website's own `/reset/<token>` page"
    ),
)
async def forgot_password(
    payload: ForgotPasswordRequest, use_case: RequestClubPasswordResetDep
) -> Response:
    await use_case.execute(payload.email)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post(
    "/forgot-password/claim",
    response_model=ClaimTicketResponse,
    status_code=status.HTTP_200_OK,
    responses=CLAIM_RESPONSES,
    summary="Exchange the club's emailed code for a ticket",
    description=claim_description(),
)
async def claim_reset_code(
    payload: ClaimCodeRequest, use_case: ClaimClubPasswordResetDep
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
    summary="Set the club's new password, sign out everywhere, and sign in",
    description=new_password_description("browser"),
)
async def set_new_password(
    payload: NewPasswordRequest, use_case: SetNewClubPasswordDep
) -> TokenResponse:
    pair = await use_case.execute(
        SetNewPasswordCommand(
            password=payload.password, token=payload.token, ticket=payload.ticket
        )
    )
    return TokenResponse.from_pair(pair)
