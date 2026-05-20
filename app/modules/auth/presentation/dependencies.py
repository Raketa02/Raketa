from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.infrastructure.database.session import get_db
from app.infrastructure.database.unit_of_work import AsyncSqlAlchemyUnitOfWork
from app.modules.auth.application.login import Login
from app.modules.auth.application.logout import Logout
from app.modules.auth.application.refresh_token import RefreshAuthTokens
from app.modules.auth.application.token_rotation import TokenRotator
from app.modules.auth.domain.ports import (
    PasswordHasher,
    RefreshTokenRepository,
    TokenService,
)
from app.modules.auth.infrastructure.jwt_token_service import JwtTokenService
from app.modules.auth.infrastructure.password_hasher import BcryptPasswordHasher
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from app.modules.users.infrastructure.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from app.shared.clock import Clock, SystemClock


def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def get_token_service(settings: Settings = Depends(get_settings)) -> TokenService:
    return JwtTokenService(settings)


def get_clock() -> Clock:
    return SystemClock()


def get_refresh_token_repository(
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(db)


def get_token_rotator(
    db: AsyncSession = Depends(get_db),
    tokens: RefreshTokenRepository = Depends(get_refresh_token_repository),
    jwt_service: TokenService = Depends(get_token_service),
    hasher: PasswordHasher = Depends(get_password_hasher),
    clock: Clock = Depends(get_clock),
) -> TokenRotator:
    return TokenRotator(
        tokens=tokens,
        jwt=jwt_service,
        hasher=hasher,
        uow=AsyncSqlAlchemyUnitOfWork(db),
        clock=clock,
    )


def get_login_use_case(
    db: AsyncSession = Depends(get_db),
    hasher: PasswordHasher = Depends(get_password_hasher),
    rotator: TokenRotator = Depends(get_token_rotator),
) -> Login:
    return Login(
        users=SqlAlchemyUserRepository(db),
        hasher=hasher,
        rotator=rotator,
    )


def get_refresh_use_case(
    db: AsyncSession = Depends(get_db),
    tokens: RefreshTokenRepository = Depends(get_refresh_token_repository),
    jwt_service: TokenService = Depends(get_token_service),
    hasher: PasswordHasher = Depends(get_password_hasher),
    rotator: TokenRotator = Depends(get_token_rotator),
    clock: Clock = Depends(get_clock),
) -> RefreshAuthTokens:
    return RefreshAuthTokens(
        users=SqlAlchemyUserRepository(db),
        tokens=tokens,
        jwt_service=jwt_service,
        hasher=hasher,
        rotator=rotator,
        clock=clock,
    )


def get_logout_use_case(
    db: AsyncSession = Depends(get_db),
    tokens: RefreshTokenRepository = Depends(get_refresh_token_repository),
    jwt_service: TokenService = Depends(get_token_service),
    hasher: PasswordHasher = Depends(get_password_hasher),
    clock: Clock = Depends(get_clock),
) -> Logout:
    return Logout(
        tokens=tokens,
        jwt_service=jwt_service,
        hasher=hasher,
        uow=AsyncSqlAlchemyUnitOfWork(db),
        clock=clock,
    )
