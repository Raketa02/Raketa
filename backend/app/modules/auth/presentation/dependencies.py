from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    MailQueueDep,
    OneTimeCredentialsDep,
    PasswordHasherDep,
    RefreshTokenRepositoryDep,
    SettingsDep,
    SignOutEverywhereDep,
    TokenRotatorDep,
    TokenServiceDep,
    UnitOfWorkDep,
    UserRepositoryDep,
)
from app.bootstrap.composition import (
    build_user_password_accounts,
    build_user_session_holders,
)
from app.modules.auth.application.forgot_password import (
    ClaimPasswordReset,
    RequestPasswordReset,
    SetNewPassword,
)
from app.modules.auth.application.login import Login
from app.modules.auth.application.logout import Logout
from app.modules.auth.application.refresh_token import RefreshAuthTokens
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.password_reset import ResetPage
from app.modules.auth.domain.ports import PasswordAccounts, SessionHolders


def get_login_use_case(
    users: UserRepositoryDep,
    hasher: PasswordHasherDep,
    rotator: TokenRotatorDep,
) -> Login:
    return Login(
        users=users,
        hasher=hasher,
        rotator=rotator,
    )


LoginUseCaseDep = Annotated[Login, Depends(get_login_use_case)]


def get_player_session_holders(db: DbSession) -> SessionHolders:
    return build_user_session_holders(db)


PlayerSessionHoldersDep = Annotated[SessionHolders, Depends(get_player_session_holders)]


def get_refresh_use_case(
    holders: PlayerSessionHoldersDep,
    tokens: RefreshTokenRepositoryDep,
    jwt_service: TokenServiceDep,
    hasher: PasswordHasherDep,
    rotator: TokenRotatorDep,
    clock: ClockDep,
) -> RefreshAuthTokens:
    return RefreshAuthTokens(
        audience=Audience.PLAYER_APP,
        holders=holders,
        tokens=tokens,
        jwt_service=jwt_service,
        hasher=hasher,
        rotator=rotator,
        clock=clock,
    )


RefreshUseCaseDep = Annotated[RefreshAuthTokens, Depends(get_refresh_use_case)]


def get_logout_use_case(
    tokens: RefreshTokenRepositoryDep,
    jwt_service: TokenServiceDep,
    hasher: PasswordHasherDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
    events: EventPublisherDep,
) -> Logout:
    return Logout(
        audience=Audience.PLAYER_APP,
        tokens=tokens,
        jwt_service=jwt_service,
        hasher=hasher,
        uow=uow,
        clock=clock,
        events=events,
    )


LogoutUseCaseDep = Annotated[Logout, Depends(get_logout_use_case)]


# --- Forgot password?, for the player app (docs/adr/0184 §5) -------------------


def get_player_password_accounts(
    db: DbSession, event_store: DomainEventStoreDep, events: EventPublisherDep
) -> PasswordAccounts:
    return build_user_password_accounts(db, event_store=event_store, events=events)


PlayerPasswordAccountsDep = Annotated[
    PasswordAccounts, Depends(get_player_password_accounts)
]


def get_request_password_reset(
    accounts: PlayerPasswordAccountsDep,
    credentials: OneTimeCredentialsDep,
    mail: MailQueueDep,
    settings: SettingsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> RequestPasswordReset:
    return RequestPasswordReset(
        audience=Audience.PLAYER_APP,
        accounts=accounts,
        credentials=credentials,
        mail=mail,
        # A player's or an administrator's link opens the public site's page.
        reset_page=ResetPage(settings.PUBLIC_SITE_URL),
        uow=uow,
        clock=clock,
    )


RequestPasswordResetDep = Annotated[
    RequestPasswordReset, Depends(get_request_password_reset)
]


def get_claim_password_reset(
    credentials: OneTimeCredentialsDep, uow: UnitOfWorkDep, clock: ClockDep
) -> ClaimPasswordReset:
    return ClaimPasswordReset(
        audience=Audience.PLAYER_APP, credentials=credentials, uow=uow, clock=clock
    )


ClaimPasswordResetDep = Annotated[
    ClaimPasswordReset, Depends(get_claim_password_reset)
]


def get_set_new_password(
    accounts: PlayerPasswordAccountsDep,
    credentials: OneTimeCredentialsDep,
    sign_out_everywhere: SignOutEverywhereDep,
    hasher: PasswordHasherDep,
    rotator: TokenRotatorDep,
    clock: ClockDep,
) -> SetNewPassword:
    return SetNewPassword(
        audience=Audience.PLAYER_APP,
        accounts=accounts,
        credentials=credentials,
        sign_out_everywhere=sign_out_everywhere,
        hasher=hasher,
        rotator=rotator,
        clock=clock,
    )


SetNewPasswordDep = Annotated[SetNewPassword, Depends(get_set_new_password)]
