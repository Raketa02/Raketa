from __future__ import annotations

from typing import Annotated, Any, Final

from fastapi import Depends, status

from app.api.dependencies import (
    ClockDep,
    DomainEventStoreDep,
    EventPublisherDep,
    PasswordHasherDep,
    TokenServiceDep,
    UnitOfWorkDep,
    UserRepositoryDep,
)
from app.core.exception_handlers import ErrorResponse
from app.core.security import BearerCredentialsDep
from app.modules.users.application.get_current_user import GetCurrentUser
from app.modules.users.application.name_user import NameUser
from app.modules.users.application.attest_adult import AttestAdult
from app.modules.users.application.read_own_account import ReadOwnAccount
from app.modules.users.application.register_user import RegisterUser
from app.modules.users.application.resolve_current_user import (
    AuthenticatedSession,
    ResolveCurrentUserFromAccessToken,
)
from app.modules.users.domain.user import User


def get_register_user(
    users: UserRepositoryDep,
    event_store: DomainEventStoreDep,
    hasher: PasswordHasherDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
    events: EventPublisherDep,
) -> RegisterUser:
    return RegisterUser(
        users=users,
        event_store=event_store,
        hasher=hasher,
        uow=uow,
        clock=clock,
        events=events,
    )


RegisterUserDep = Annotated[RegisterUser, Depends(get_register_user)]


def get_name_user(
    users: UserRepositoryDep,
    event_store: DomainEventStoreDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
    events: EventPublisherDep,
) -> NameUser:
    return NameUser(
        users=users, event_store=event_store, uow=uow, clock=clock, events=events
    )


NameUserDep = Annotated[NameUser, Depends(get_name_user)]


def get_read_own_account(event_store: DomainEventStoreDep) -> ReadOwnAccount:
    return ReadOwnAccount(event_store=event_store)


ReadOwnAccountDep = Annotated[ReadOwnAccount, Depends(get_read_own_account)]


def get_attest_adult(
    event_store: DomainEventStoreDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
    events: EventPublisherDep,
) -> AttestAdult:
    return AttestAdult(event_store=event_store, uow=uow, clock=clock, events=events)


AttestAdultDep = Annotated[AttestAdult, Depends(get_attest_adult)]


def get_current_user_use_case(
    users: UserRepositoryDep,
) -> GetCurrentUser:
    return GetCurrentUser(users=users)


GetCurrentUserUseCaseDep = Annotated[GetCurrentUser, Depends(get_current_user_use_case)]


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


async def authenticated_session(
    credentials: BearerCredentialsDep,
    use_case: ResolveCurrentUserUseCaseDep,
) -> AuthenticatedSession:
    """Who is calling, **and until when.**

    Declared beside ``current_user`` rather than instead of it: one route in this
    application cares when its caller's credential runs out — the conversation
    stream, which closes at that instant (``docs/adr/0147`` §6) — and every other
    route wants the user and would have to ignore a deadline.
    """

    token = credentials.credentials if credentials else None
    return await use_case.authenticated_session(token)


#: Spelled ``Authenticated…`` and never ``CurrentSession``, because *session* in
#: this codebase means an ``AsyncSession``: one route declares both, and two
#: parameters called ``session`` and ``db`` would be the wrong way round the
#: first time somebody edited it.
AuthenticatedSessionDep = Annotated[
    AuthenticatedSession, Depends(authenticated_session)
]


async def current_user(
    credentials: BearerCredentialsDep,
    use_case: ResolveCurrentUserUseCaseDep,
) -> User:
    token = credentials.credentials if credentials else None
    return await use_case.execute(token)


CurrentUserDep = Annotated[User, Depends(current_user)]


async def attested_player(user: CurrentUserDep, own: ReadOwnAccountDep) -> User:
    """The signed-in account, **refused unless it has given the Adult
    attestation** (``docs/adr/0185`` §5) — what the two acts a player-side
    record begins with take instead of ``CurrentUserDep``: starting an
    assessment, and committing a Player profile. One stream read, on two routes
    a player meets once per sport and once."""

    await own.refuse_unless_attested(user.id)
    return user


AttestedPlayerDep = Annotated[User, Depends(attested_player)]

#: What a route taking ``AttestedPlayerDep`` declares beside its own refusals.
ADULT_ATTESTATION_MISSING: Final[dict[int | str, dict[str, Any]]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`adult_attestation_missing` — this account has not given the Adult "
            "attestation, which playing requires: an account an invitation "
            "opened, before *Start playing*'s first step."
        ),
    },
}
