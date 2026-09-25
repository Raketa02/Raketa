from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    EventPublisherDep,
    PasswordHasherDep,
    RefreshTokenRepositoryDep,
    TokenRotatorDep,
    TokenServiceDep,
    UnitOfWorkDep,
    UserRepositoryDep,
)
from app.bootstrap.composition import build_user_session_holders
from app.modules.auth.application.login import Login
from app.modules.auth.application.logout import Logout
from app.modules.auth.application.refresh_token import RefreshAuthTokens
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.ports import SessionHolders


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
