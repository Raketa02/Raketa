from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    EventPublisherDep,
    PasswordHasherDep,
    RefreshTokenRepositoryDep,
    TokenRotatorDep,
    TokenServiceDep,
    UnitOfWorkDep,
    UserRepositoryDep,
)
from app.modules.auth.application.login import Login
from app.modules.auth.application.logout import Logout
from app.modules.auth.application.refresh_token import RefreshAuthTokens


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


def get_refresh_use_case(
    users: UserRepositoryDep,
    tokens: RefreshTokenRepositoryDep,
    jwt_service: TokenServiceDep,
    hasher: PasswordHasherDep,
    rotator: TokenRotatorDep,
    clock: ClockDep,
) -> RefreshAuthTokens:
    return RefreshAuthTokens(
        users=users,
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
        tokens=tokens,
        jwt_service=jwt_service,
        hasher=hasher,
        uow=uow,
        clock=clock,
        events=events,
    )


LogoutUseCaseDep = Annotated[Logout, Depends(get_logout_use_case)]
