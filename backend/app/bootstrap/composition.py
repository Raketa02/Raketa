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
from app.modules.courts.application.claim_court import ClaimCourt
from app.modules.courts.domain.ports import (
    BookingRepository,
    ReservationRepository,
)
from app.modules.courts.infrastructure.sqlalchemy_booking_repository import (
    SqlAlchemyBookingRepository,
)
from app.modules.matches.domain.ports import CourtHolds, MatchRepository
from app.modules.now.domain.ports import RatedSports
from app.modules.now.infrastructure.rating_sports import RatedSportsFromSkillRatings
from app.modules.matches.infrastructure.court_holds import (
    CourtHoldsThroughReservations,
)
from app.modules.matches.infrastructure.sqlalchemy_match_repository import (
    SqlAlchemyMatchRepository,
)
from app.modules.courts.infrastructure.sqlalchemy_reservation_repository import (
    SqlAlchemyReservationRepository,
)
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


# --------------------------------------------------------------------------
# Courts and Bookings
# --------------------------------------------------------------------------


def build_reservation_repository(session: AsyncSession) -> ReservationRepository:
    """The record repository, over `session`.

    A session rather than its own ports, for the reason the club's takes one: a
    reservation is rows, the concurrency guard is a column, and there is no
    event store to share. What this adapter *does* need a session for beyond the
    obvious is the savepoint it opens around every claim — the exclusion
    constraint's refusal has to be scoped so the caller can look again.
    """
    return SqlAlchemyReservationRepository(session)


def build_booking_repository(session: AsyncSession) -> BookingRepository:
    return SqlAlchemyBookingRepository(session)


# --------------------------------------------------------------------------
# Matches
# --------------------------------------------------------------------------


def build_match_repository(
    session: AsyncSession, *, events: DomainEventPublisher
) -> MatchRepository:
    """The record repository, over `session` — **and its publisher**.

    The only record repository here that takes a publisher, and ADR-0034 is why:
    Matches keeps no history, so its announcements are the whole trail, and they
    have to be written in the transaction that wrote the row. Clubs needs none
    (nothing has to react to a policy change) and Courts needs none yet
    (ADR-0071 narrows the pattern to *a named future reader*). This context has
    a named future reader, and it is the planned playerEventsTracker.

    The publisher is an argument rather than built here so that a caller sharing
    one outbox writer across two contexts — which `Raketa02/Raketa#70` will do —
    passes it in rather than getting a second one by accident.
    """
    return SqlAlchemyMatchRepository(session, events=events)


def build_court_holds(
    claim: ClaimCourt, reservations: ReservationRepository
) -> CourtHolds:
    """The hold ladder's way of asking Courts for a court, and giving it back.

    Takes the Courts context's own claim **use case** rather than rebuilding its
    scan: ADR-0035's re-ask loop is the answer to *which court*, and a second one
    here would be a second answer that agrees only until one of them is fixed.
    `ClaimCourt.claim` deliberately does not commit, which is what lets a seat
    payment, the court it earns and both outbox rows be one write.
    """
    return CourtHoldsThroughReservations(claim=claim, reservations=reservations)


# --------------------------------------------------------------------------
# Now
# --------------------------------------------------------------------------


def build_rated_sports(ratings: SkillRatingRepository) -> RatedSports:
    """`Now`'s answer to *which sports does this player hold a rating at*.

    Takes the rating context's **port** rather than a session: what backs a
    rating is the rating context's business, and the day a projection answers
    this faster than a replay does, only this line moves.
    """
    return RatedSportsFromSkillRatings(ratings=ratings)
