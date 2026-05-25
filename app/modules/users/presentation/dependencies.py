from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies import (
    ClockDep,
    EventPublisherDep,
    PasswordHasherDep,
    TokenServiceDep,
    UnitOfWorkDep,
    UserRepositoryDep,
)
from app.core.security import bearer_scheme
from app.modules.users.application.get_current_user import GetCurrentUser
from app.modules.users.application.register_user import RegisterUser
from app.modules.users.application.resolve_current_user import (
    ResolveCurrentUserFromAccessToken,
)
from app.modules.users.domain.user import User


def get_register_user(
    users: UserRepositoryDep,
    hasher: PasswordHasherDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
    events: EventPublisherDep,
) -> RegisterUser:
    return RegisterUser(
        users=users,
        hasher=hasher,
        uow=uow,
        clock=clock,
        events=events,
    )


RegisterUserDep = Annotated[RegisterUser, Depends(get_register_user)]


def get_current_user_use_case(
    users: UserRepositoryDep,
) -> GetCurrentUser:
    return GetCurrentUser(users=users)


GetCurrentUserUseCaseDep = Annotated[
    GetCurrentUser, Depends(get_current_user_use_case)
]


def get_resolve_current_user_use_case(
    token_service: TokenServiceDep,
    get_current_user: GetCurrentUserUseCaseDep,
) -> ResolveCurrentUserFromAccessToken:
    return ResolveCurrentUserFromAccessToken(
        token_service=token_service,
        get_current_user=get_current_user,
    )


ResolveCurrentUserUseCaseDep = Annotated[
    ResolveCurrentUserFromAccessToken, Depends(get_resolve_current_user_use_case)
]

BearerCredentialsDep = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]


async def current_user(
    credentials: BearerCredentialsDep,
    use_case: ResolveCurrentUserUseCaseDep,
) -> User:
    token = credentials.credentials if credentials else None
    return await use_case.execute(token)


CurrentUserDep = Annotated[User, Depends(current_user)]
