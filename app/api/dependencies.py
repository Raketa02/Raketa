from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.infrastructure.database.session import get_db
from app.infrastructure.database.unit_of_work import (
    AsyncSqlAlchemyUnitOfWork,
    UnitOfWork,
)
from app.infrastructure.events.sqlalchemy_outbox_repository import (
    SqlAlchemyOutboxRepository,
)
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
from app.shared.events import (
    DomainEventPublisher,
    EventRegistry,
    OutboxEventPublisher,
    OutboxRepository,
)

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


def get_event_registry(request: Request) -> EventRegistry:
    return request.app.state.event_registry


EventRegistryDep = Annotated[EventRegistry, Depends(get_event_registry)]


def get_outbox_repository(db: DbSession) -> OutboxRepository:
    return SqlAlchemyOutboxRepository(db)


OutboxRepositoryDep = Annotated[OutboxRepository, Depends(get_outbox_repository)]


def get_event_publisher(
    outbox: OutboxRepositoryDep,
    registry: EventRegistryDep,
    clock: ClockDep,
) -> DomainEventPublisher:
    return OutboxEventPublisher(outbox=outbox, registry=registry, clock=clock)


EventPublisherDep = Annotated[DomainEventPublisher, Depends(get_event_publisher)]


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
