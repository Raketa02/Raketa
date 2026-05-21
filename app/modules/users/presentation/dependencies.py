from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import bearer_scheme
from app.infrastructure.database.session import get_db
from app.infrastructure.database.unit_of_work import AsyncSqlAlchemyUnitOfWork
from app.modules.auth.infrastructure.password_hasher import BcryptPasswordHasher
from app.modules.auth.domain.ports import TokenService
from app.modules.auth.presentation.dependencies import get_token_service
from app.modules.users.application.get_current_user import GetCurrentUser
from app.modules.users.application.register_user import RegisterUser
from app.modules.users.application.resolve_current_user import (
    ResolveCurrentUserFromAccessToken,
)
from app.modules.users.domain.user import User
from app.modules.users.infrastructure.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(db)


def get_register_user(
    db: AsyncSession = Depends(get_db),
    users: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> RegisterUser:
    return RegisterUser(
        users=users,
        hasher=BcryptPasswordHasher(),
        uow=AsyncSqlAlchemyUnitOfWork(db),
    )


def get_get_current_user_use_case(
    users: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> GetCurrentUser:
    return GetCurrentUser(users=users)


def get_resolve_current_user_use_case(
    token_service: TokenService = Depends(get_token_service),
    get_current_user: GetCurrentUser = Depends(get_get_current_user_use_case),
) -> ResolveCurrentUserFromAccessToken:
    return ResolveCurrentUserFromAccessToken(
        token_service=token_service,
        get_current_user=get_current_user,
    )


async def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    use_case: ResolveCurrentUserFromAccessToken = Depends(
        get_resolve_current_user_use_case
    ),
) -> User:
    token = credentials.credentials if credentials else None
    return await use_case.execute(token)
