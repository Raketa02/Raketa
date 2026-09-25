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
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import (
    DomainEventPublisher,
    DomainEventStore,
    MailQueue,
    UnitOfWork,
)
from app.bootstrap.composition import (
    build_clock,
    build_credential_secrets,
    build_domain_event_store,
    build_event_publisher,
    build_mail_queue,
    build_one_time_credential_store,
    build_password_hasher,
    build_refresh_token_repository,
    build_token_service,
    build_unit_of_work,
    build_user_repository,
)
from app.bootstrap.events import EventRuntime, get_event_runtime
from app.core.config import Settings, get_settings
from app.infrastructure.database.session import get_db
from app.infrastructure.redis_client import get_redis
from app.kernel import Clock
from app.modules.auth.application.one_time_credentials import OneTimeCredentials
from app.modules.auth.application.sign_out_everywhere import SignOutEverywhere
from app.modules.auth.application.token_rotation import TokenRotator
from app.modules.auth.domain.ports import (
    PasswordHasher,
    RefreshTokenRepository,
    TokenService,
)
from app.modules.users.domain.ports import UserRepository

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_password_hasher(settings: SettingsDep) -> PasswordHasher:
    return build_password_hasher(settings)


PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]


def get_clock() -> Clock:
    return build_clock()


ClockDep = Annotated[Clock, Depends(get_clock)]


def get_token_service(settings: SettingsDep, clock: ClockDep) -> TokenService:
    # On the request's clock, so a token's issue instant and the account's
    # credentials-changed instant are read off one clock (``docs/adr/0185`` §7).
    return build_token_service(settings, clock=clock)


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]

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


def get_mail_queue(db: DbSession) -> MailQueue:
    return build_mail_queue(db)


MailQueueDep = Annotated[MailQueue, Depends(get_mail_queue)]


def get_one_time_credentials(
    db: DbSession, hasher: PasswordHasherDep
) -> OneTimeCredentials:
    # The one credential mechanism both surfaces issue and redeem through
    # (``docs/adr/0184`` §3), composed from ports as the rotator is.
    return OneTimeCredentials(
        store=build_one_time_credential_store(db),
        secrets=build_credential_secrets(),
        hasher=hasher,
    )


OneTimeCredentialsDep = Annotated[
    OneTimeCredentials, Depends(get_one_time_credentials)
]


def get_sign_out_everywhere(
    tokens: RefreshTokenRepositoryDep, events: EventPublisherDep
) -> SignOutEverywhere:
    return SignOutEverywhere(tokens=tokens, events=events)


SignOutEverywhereDep = Annotated[SignOutEverywhere, Depends(get_sign_out_everywhere)]


def get_ephemeral_store_or_nothing() -> Redis | None:
    """The process's Redis pool, or nothing where it never came up.

    **``None`` rather than a raise**, which is the one place this differs from
    the matcher's ``EphemeralStoreDep`` — that declaration's name for the
    opposite posture, and the reason this one is not called that. A search that
    cannot read its ledgers is a search that cannot answer; the routes that ask
    for this answer regardless, and a store that is not there reaches the
    reader as *the pairing could not be read* rather than as a failed screen
    (``docs/adr/0143`` §6, ``docs/adr/0161``). Two contexts declare that
    posture — a challenge's detail and a game's pairing — so it is declared
    once, here, beside the other platform-wide seams. It stays a ``Depends`` so
    a test can override it.
    """

    try:
        return get_redis()
    except RuntimeError:
        return None


StoreOrNothingDep = Annotated[Redis | None, Depends(get_ephemeral_store_or_nothing)]
