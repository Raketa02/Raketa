"""Request-scoped declarations over the framework-free factories.

This module answers *when* an adapter is built and how long it lives — one per
request, cached by FastAPI for that request's duration. It does not answer what
is built: every adapter comes from `app.bootstrap.composition`, so the wiring a
seed run or a worker gets is the wiring a request gets, rather than a copy of it.

Nothing here constructs an adapter, and `tests/unit/test_composition_root.py`
asserts that structurally. The one infrastructure import that remains is
`get_db`, which is not an adapter but the request-scoped session itself — the
single thing in this file that genuinely belongs to the request.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.bootstrap.composition import (
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_password_hasher,
    build_refresh_token_repository,
    build_token_service,
    build_unit_of_work,
    build_user_repository,
)
from app.bootstrap.events import EventRuntime, get_event_runtime
from app.core.config import Settings, get_settings
from app.infrastructure.database.session import get_db
from app.kernel import Clock
from app.modules.auth.application.token_rotation import TokenRotator
from app.modules.auth.domain.ports import (
    PasswordHasher,
    RefreshTokenRepository,
    TokenService,
)
from app.modules.users.domain.ports import UserRepository

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_password_hasher() -> PasswordHasher:
    return build_password_hasher()


PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]


def get_token_service(settings: SettingsDep) -> TokenService:
    return build_token_service(settings)


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


def get_clock() -> Clock:
    return build_clock()


ClockDep = Annotated[Clock, Depends(get_clock)]

# The runtime is the process's, not the request's — `get_event_runtime` takes no
# request and reads no application state. It stays a `Depends` so that a test can
# still override it for one app.
EventRuntimeDep = Annotated[EventRuntime, Depends(get_event_runtime)]


def get_event_publisher(
    db: DbSession,
    runtime: EventRuntimeDep,
) -> DomainEventPublisher:
    return build_event_publisher(db, runtime=runtime)


EventPublisherDep = Annotated[DomainEventPublisher, Depends(get_event_publisher)]


def get_domain_event_store(
    db: DbSession,
    runtime: EventRuntimeDep,
) -> DomainEventStore:
    return build_domain_event_store(db, runtime=runtime)


DomainEventStoreDep = Annotated[DomainEventStore, Depends(get_domain_event_store)]


def get_user_repository(db: DbSession) -> UserRepository:
    return build_user_repository(db)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_refresh_token_repository(db: DbSession) -> RefreshTokenRepository:
    return build_refresh_token_repository(db)


RefreshTokenRepositoryDep = Annotated[
    RefreshTokenRepository, Depends(get_refresh_token_repository)
]


def get_unit_of_work(db: DbSession) -> UnitOfWork:
    return build_unit_of_work(db)


UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]


def get_token_rotator(
    tokens: RefreshTokenRepositoryDep,
    jwt_service: TokenServiceDep,
    hasher: PasswordHasherDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
    events: EventPublisherDep,
) -> TokenRotator:
    # Composed from ports rather than constructed from adapters, so it is a
    # declaration like the use cases below it and not a factory's business.
    return TokenRotator(
        tokens=tokens,
        jwt=jwt_service,
        hasher=hasher,
        uow=uow,
        clock=clock,
        events=events,
    )


TokenRotatorDep = Annotated[TokenRotator, Depends(get_token_rotator)]
