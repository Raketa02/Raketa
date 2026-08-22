"""Adapter construction, with no web framework in it.

Every port a use case depends on is built here by a plain function whose
arguments are a database session, the settings, or ports built by the functions
above it. Nothing in this module imports FastAPI, and nothing in it reads a
request.

**The rule this module exists to make true: an adapter is a function of a
session and configuration, and only the *declaration* of that function ever
belonged to the web layer.** Before it, every adapter was constructed inside a
`Depends` callable, so anything that is not an HTTP request — a seed run, a
worker, a management command — had two options, and both are bad. Boot the API
to create data, or hand-copy the wiring into a second composition root. A
hand-copied composition root drifts from the real one silently: it keeps
working, and it stops being the thing production runs.

`app/api/dependencies.py` and each module's `presentation/dependencies.py` are
now thin callers over these functions. They declare *when* an adapter is built
and how long it lives; this module decides *what* is built. A test asserts the
split structurally — those modules import no adapter — because the failure mode
is one line of convenience in a `Depends` callable, and nothing about a green
suite would look different afterwards.

Sharing is the caller's business, deliberately. Each function returns a new
instance, and every adapter here is a stateless wrapper over the session, so
two instances over one session are interchangeable. Under FastAPI the sharing
comes free: it caches each dependency for the life of a request, so the store
one repository is given is the store the other is given. A caller outside a
request that wants the same guarantee builds a port once and passes it on, the
way `build_assessment_repository` takes its two.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.bootstrap.events import EventRuntime, get_event_runtime
from app.core.config import Settings
from app.engines.assessment import AssessmentEngine
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.infrastructure.clock import SystemClock
from app.infrastructure.database.unit_of_work import AsyncSqlAlchemyUnitOfWork
from app.kernel import Clock
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
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.clubs.infrastructure.sqlalchemy_club_repository import (
    SqlAlchemyClubRepository,
)
from app.modules.rating.domain.ports import AssessmentRepository, SkillRatingRepository
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    EventSourcedAssessmentRepository,
)
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    EventSourcedSkillRatingRepository,
)
from app.modules.users.domain.ports import UserRepository
from app.modules.users.infrastructure.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)

# --------------------------------------------------------------------------
# Cross-cutting adapters
# --------------------------------------------------------------------------


def build_clock() -> Clock:
    return SystemClock()


def build_unit_of_work(session: AsyncSession) -> UnitOfWork:
    return AsyncSqlAlchemyUnitOfWork(session)


def build_domain_event_store(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> DomainEventStore:
    """The append-only aggregate event stream, over `session`.

    `runtime` defaults to the process's, so a caller holding only a session can
    build one. It stays an argument because the event runtime is the one piece
    of this wiring a caller might legitimately replace — a worker driving a
    narrowed catalog, a test standing up its own dispatcher — and a default is
    not the same as a decision taken for everybody.
    """
    return (runtime or get_event_runtime()).create_domain_event_store_for(
        session=session
    )


def build_event_publisher(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> DomainEventPublisher:
    """The transactional outbox writer, over `session`. See the store above."""
    return (runtime or get_event_runtime()).create_publisher_for(session=session)


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------


def build_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def build_token_service(settings: Settings) -> TokenService:
    return JwtTokenService(settings)


def build_refresh_token_repository(session: AsyncSession) -> RefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(session)


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------


def build_user_repository(session: AsyncSession) -> UserRepository:
    return SqlAlchemyUserRepository(session)


# --------------------------------------------------------------------------
# Rating
# --------------------------------------------------------------------------


def build_assessment_engine() -> AssessmentEngine:
    """The concrete engine version is chosen here, and nowhere else.

    Use cases depend on the `AssessmentEngine` abstraction, so a version swap is
    a one-line change — and it is one line rather than one per composition root,
    which is the point of this module. A seed run replaying an onboarding
    assessment gets the version the API is serving, by construction.
    """
    return RacketSkillEngineV3()


def build_assessment_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> AssessmentRepository:
    """Takes its two ports rather than a session, so a caller decides what is
    shared. The repository remembers the stream versions it loaded, so it is
    never longer-lived than the unit of work it was built beside: one request's
    versions must never answer for another's.
    """
    return EventSourcedAssessmentRepository(event_store=event_store, events=events)


def build_skill_rating_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> SkillRatingRepository:
    """Per unit of work, for the same reason the assessment's is."""
    return EventSourcedSkillRatingRepository(event_store=event_store, events=events)


# --------------------------------------------------------------------------
# Clubs
# --------------------------------------------------------------------------


def build_club_repository(session: AsyncSession) -> ClubRepository:
    """The record repository, over `session`.

    Takes a session rather than its own ports because a club is rows rather than
    a stream: there is no event store to share and no version bookkeeping to keep
    per unit of work — the guard is a column, compared in the UPDATE that bumps
    it.
    """
    return SqlAlchemyClubRepository(session)
