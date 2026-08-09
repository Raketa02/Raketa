from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.bootstrap.events import EventRuntime
from app.core.config import Settings, get_settings
from app.infrastructure.database.session import get_db
from app.infrastructure.database.unit_of_work import AsyncSqlAlchemyUnitOfWork
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
from app.modules.users.domain.ports import UserRepository
from app.modules.users.infrastructure.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from app.shared.clock import Clock, SystemClock

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]


def get_token_service(settings: SettingsDep) -> TokenService:
    return JwtTokenService(settings)


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


def get_clock() -> Clock:
    return SystemClock()


ClockDep = Annotated[Clock, Depends(get_clock)]


def get_event_runtime(request: Request) -> EventRuntime:
    return request.app.state.event_runtime


EventRuntimeDep = Annotated[EventRuntime, Depends(get_event_runtime)]


def get_event_publisher(
    db: DbSession,
    runtime: EventRuntimeDep,
) -> DomainEventPublisher:
    return runtime.create_publisher_for(session=db)


EventPublisherDep = Annotated[DomainEventPublisher, Depends(get_event_publisher)]


def get_domain_event_store(
    db: DbSession,
    runtime: EventRuntimeDep,
) -> DomainEventStore:
    return runtime.create_domain_event_store_for(session=db)


DomainEventStoreDep = Annotated[DomainEventStore, Depends(get_domain_event_store)]


def get_user_repository(db: DbSession) -> UserRepository:
    return SqlAlchemyUserRepository(db)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_refresh_token_repository(db: DbSession) -> RefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(db)


RefreshTokenRepositoryDep = Annotated[
    RefreshTokenRepository, Depends(get_refresh_token_repository)
]


def get_unit_of_work(db: DbSession) -> UnitOfWork:
    return AsyncSqlAlchemyUnitOfWork(db)


UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]


def get_token_rotator(
    tokens: RefreshTokenRepositoryDep,
    jwt_service: TokenServiceDep,
    hasher: PasswordHasherDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
    events: EventPublisherDep,
) -> TokenRotator:
    return TokenRotator(
        tokens=tokens,
        jwt=jwt_service,
        hasher=hasher,
        uow=uow,
        clock=clock,
        events=events,
    )


TokenRotatorDep = Annotated[TokenRotator, Depends(get_token_rotator)]
