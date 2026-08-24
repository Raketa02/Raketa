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

from app.application.ports import (
    CommandLog,
    DomainEventPublisher,
    DomainEventStore,
    UnitOfWork,
)
from app.bootstrap.events import EventRuntime, get_event_runtime
from app.core.config import Settings
from app.engines.assessment import AssessmentEngine
from app.engines.matchfit.v1 import MatchFitEngineV1
from app.engines.pairing.v1 import PairingEngineV1
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.infrastructure.clock import SystemClock
from app.infrastructure.database.sqlalchemy_command_log import SqlAlchemyCommandLog
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
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.application.standby import JoinStandby
from app.modules.matches.application.take_match_wake import (
    MatchWakeBatch,
    TakeMatchWake,
)
from app.modules.matches.domain.ports import (
    CourtHolds,
    MatchRepository,
    MatchSchedule,
    SeatClaims,
)
from app.modules.matches.domain.ports import StandbyPlaces as MatchStandbyPlaces
from app.modules.money.domain.ports import LedgerRepository, Seats
from app.modules.money.infrastructure.event_sourced_ledger_repository import (
    EventSourcedLedgerRepository,
)
from app.modules.money.infrastructure.seats_through_matches import SeatsThroughMatches
from app.modules.now.application.compose_enrolled import ComposeEnrolled
from app.modules.now.application.departure import MakeDeparture, ReadDeparture
from app.modules.now.application.result import (
    AcceptResult,
    ProposeResult,
    ReadResult,
)
from app.modules.now.application.cascade import (
    CascadeBatch,
    OpenCascade,
    RunCascade,
)
from app.modules.now.application.standby import LeaveStandby
from app.modules.now.application.compose_shelves import ComposeShelves
from app.modules.now.application.new_arrivals import ComposeNewArrivals
from app.modules.now.application.scoring import MatchScorer
from app.modules.now.domain.ports import (
    ArrivalRows,
    ArrivalSets,
    CityMatches,
    Commitments,
    Departures,
    EnrolledMatches,
    Levels,
    NewArrivals,
    ParkedRuns,
    RatedSports,
    Ratings,
    Results,
    CascadeWaves,
    ClubRegulars,
    Offers,
    RatedPlayers,
    ScoringContexts,
    Standby,
    StandbyPlaces,
    StandbyQueue,
)
from app.modules.now.infrastructure.arrival_sets import InMemoryArrivalSets
from app.modules.now.infrastructure.city_matches import CityMatchesFromMatches
from app.modules.now.infrastructure.commitments import CommitmentsFromMatches
from app.modules.now.infrastructure.departures_through_matches import (
    DeparturesThroughMatches,
)
from app.modules.now.infrastructure.enrolled_matches import EnrolledFromMatches
from app.modules.now.infrastructure.levels import LevelsFromSkillRatings
from app.modules.now.infrastructure.new_arrivals import ArrivalsFromUsersAndClubs
from app.modules.now.infrastructure.parked_runs import ParkedRunsFromAssessments
from app.modules.now.infrastructure.rating_sports import RatedSportsFromSkillRatings
from app.modules.now.infrastructure.ratings import RatingsFromSkillRatings
from app.modules.now.infrastructure.results_through_matches import (
    ResultsThroughMatches,
)
from app.modules.now.infrastructure.scoring_contexts import InMemoryScoringContexts
from app.modules.now.infrastructure.cascade_stores import (
    SqlAlchemyCascadeWaves,
    SqlAlchemyOffers,
)
from app.modules.now.infrastructure.pool_sources import (
    ClubRegularsFromMatches,
    RatedPlayersFromRatingStreams,
)
from app.modules.now.infrastructure.standby_places import StandbyThroughMatches
from app.modules.matches.infrastructure.court_holds import (
    CourtHoldsThroughReservations,
)
from app.modules.matches.infrastructure.sqlalchemy_match_repository import (
    SqlAlchemyMatchRepository,
)
from app.modules.matches.infrastructure.sqlalchemy_match_schedule import (
    SqlAlchemyMatchSchedule,
)
from app.modules.matches.infrastructure.sqlalchemy_seat_claims import (
    SqlAlchemySeatClaims,
)
from app.modules.matches.infrastructure.sqlalchemy_standby_list import (
    SqlAlchemyStandbyPlaces,
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
    session: AsyncSession, *, events: DomainEventPublisher, clock: Clock
) -> MatchRepository:
    """The record repository, over `session` — **and its publisher**.

    The only record repository here that takes a publisher, and ADR-0034 is why:
    Matches keeps no history, so its announcements are the whole trail, and they
    have to be written in the transaction that wrote the row. Clubs needs none
    (nothing has to react to a policy change) and Courts needs none yet
    (ADR-0071 narrows the pattern to *a named future reader*). This context has
    a named future reader, and it is the planned playerEventsTracker.

    The publisher is an argument rather than built here so that a caller sharing
    one outbox writer across two contexts — which `money.PayForASeat` does, over
    Matches and Money (`Raketa02/Raketa#70`) — passes it in rather than getting a
    second one by accident.
    """
    return SqlAlchemyMatchRepository(session, events=events, clock=clock)


def build_match_schedule(session: AsyncSession) -> MatchSchedule:
    """The timekeeper's two statements over `next_wake_at` and `wake_reason`.

    Beside the repository rather than inside it, because they are two different
    questions: one loads a whole match, the other asks which ids are due. Takes
    no publisher and no clock — arming a schedule announces nothing, and the
    instant it stores is computed by the caller from the record.
    """

    return SqlAlchemyMatchSchedule(session)


def build_seat_claims(session: AsyncSession) -> SeatClaims:
    """*Is this player already buying a seat, anywhere* — one indexed read.

    A third port over the Matches tables, beside the repository and the
    schedule, for the same reason the schedule is one: the question is narrow
    and crosses matches, and answering it through the repository would mean
    loading a whole aggregate to discover a boolean. Takes no publisher and no
    clock — it writes nothing, and the instant it compares against is the
    caller's.
    """

    return SqlAlchemySeatClaims(session)


def build_match_wake_batch(
    *, session: AsyncSession, event_runtime: EventRuntime, clock: Clock
) -> MatchWakeBatch:
    """ADR-0076's timekeeper, wired from the same factories a request gets.

    *"A wake is a look"* is what makes this ordinary: the look runs the same use
    cases a tap runs, so there is no second wiring of the hold ladder and no
    worker-only path through Matches for a rule to be true on one side of and
    false on the other.
    """

    events = event_runtime.create_publisher_for(session=session)
    uow = build_unit_of_work(session)
    matches = build_match_repository(session, events=events, clock=clock)
    reservations = build_reservation_repository(session)
    schedule = build_match_schedule(session)
    holds = build_court_holds(
        ClaimCourt(build_club_repository(session), reservations, uow), reservations
    )
    return MatchWakeBatch(
        schedule=schedule,
        look=TakeMatchWake(
            matches,
            schedule,
            ResolveCourtHold(matches, holds, uow, clock),
            uow,
            clock,
        ),
        uow=uow,
        clock=clock,
    )


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


def build_parked_runs(assessments: AssessmentRepository) -> ParkedRuns:
    """`Now`'s answer to *has she already started this sport's questionnaire*.

    Takes the rating context's **port**, on the precedent `build_rated_sports`
    set: what backs a run is that context's business, and the door only needs to
    know whether one is waiting.
    """
    return ParkedRunsFromAssessments(assessments=assessments)


def build_arrivals(
    *,
    users: UserRepository,
    ratings: SkillRatingRepository,
    clubs: ClubRepository,
) -> ArrivalsFromUsersAndClubs:
    """Who arrived recently, and the rows their two inert cards print.

    One object answering **two** ports, for the reason its own docstring gives:
    they are the same eligibility rules asked at two depths, and a second class
    would be a second copy of *what counts as new here*. It takes three ports
    rather than a session, on the precedent `build_rated_sports` set.
    """
    return ArrivalsFromUsersAndClubs(users=users, ratings=ratings, clubs=clubs)


def build_levels(ratings: SkillRatingRepository) -> Levels:
    """Each player's Level at one sport, and whether answers are all of it."""
    return LevelsFromSkillRatings(ratings=ratings)


def build_arrival_sets(*, clock: Clock) -> ArrivalSets:
    """The new-arrivals cache — **not** per request, and not per session.

    Its whole value is being shared, so its lifetime is the application's: the
    caller holds one and hands it to every compose. There is no invalidation
    method to build here because the port has none, which is ADR-0068's design
    rather than an omission.
    """
    return InMemoryArrivalSets(clock=clock)


def build_compose_new_arrivals(
    *,
    arrivals: NewArrivals,
    rows: ArrivalRows,
    levels: Levels,
    sets: ArrivalSets,
) -> ComposeNewArrivals:
    """Shelves 4 and 5 — a shared set, and a per-viewer order."""
    return ComposeNewArrivals(arrivals=arrivals, rows=rows, levels=levels, sets=sets)


def build_enrolled_matches(
    *,
    matches: MatchRepository,
    standby: MatchStandbyPlaces,
    clubs: ClubRepository,
    reservations: ReservationRepository,
    users: UserRepository,
    ledgers: LedgerRepository,
) -> EnrolledMatches:
    """A player's own matches, and what six contexts say about each.

    Six **ports** rather than a session, on the precedent `build_arrivals` set:
    what backs a match, a queue place, a club, a reservation, a user or a ledger
    belongs to those contexts, and the enrolled strip only needs to be told.

    It is the widest reach in the app and it earns it: the strip is the region a
    player is committed to, and a card there prints where the game is, whether
    there is a roof, which court, what it cost, what she paid and what she is
    owed. Every one of those lives somewhere else.
    """
    return EnrolledFromMatches(
        matches=matches,
        standby=standby,
        clubs=clubs,
        reservations=reservations,
        users=users,
        ledgers=ledgers,
    )


def build_compose_enrolled(*, enrolled: EnrolledMatches) -> ComposeEnrolled:
    """The enrolled region — chronological, counted in money, one clock a card."""
    return ComposeEnrolled(enrolled=enrolled)


def build_departures(
    *, matches: MatchRepository, holds: ResolveCourtHold
) -> Departures:
    """The one write behind an action off Now (ADR-0086).

    Two ports rather than a session, like every builder around it. What is
    behind it is `Match.depart` and the hold ladder that runs before the save —
    a departure *leaves* a hold tier, so the court a match no longer earns goes
    back in the same transaction the seat is emptied in.

    **It does not commit.** The departure, its vacancy, both outbox rows and
    ADR-0030's command-log row close together, and that is the use case's
    transaction to close.
    """
    return DeparturesThroughMatches(matches=matches, holds=holds)


def build_command_log(session: AsyncSession) -> CommandLog:
    """ADR-0030's log: what a destructive command already did, for 24 hours.

    A session rather than ports, because it *is* one table and there is no
    context whose vocabulary it borrows. The twenty-four hours are applied on
    the read, and the prune runs on the write — so the table is bounded without
    a scheduler and correctness never waits on one.
    """
    return SqlAlchemyCommandLog(session)


def build_read_departure(*, enrolled: EnrolledMatches, clock: Clock) -> ReadDeparture:
    """What leaving is worth right now, and what it could still become."""
    return ReadDeparture(enrolled=enrolled, clock=clock)


def build_make_departure(
    *,
    enrolled: EnrolledMatches,
    departures: Departures,
    cascade: OpenCascade,
    log: CommandLog,
    uow: UnitOfWork,
    clock: Clock,
) -> MakeDeparture:
    """Leave, hand back this screen's answer **and** Now's update, and tell somebody.

    The cascade is a collaborator rather than a subscriber, because a hole with
    nobody told about it is a seat that dies quietly: it joins the departure's
    transaction (ADR-0061). What it does *there* is write two rows; the pool,
    the ratings and the scoring are the dispatch's, on its own queue.
    """
    return MakeDeparture(
        enrolled=enrolled,
        departures=departures,
        cascade=cascade,
        log=log,
        uow=uow,
        clock=clock,
    )


def build_offers(session: AsyncSession) -> Offers:
    """What the cascade told whom. **The first table Now owns.**

    A session rather than ports, because it *is* one table — the shape
    `build_command_log` and `build_match_standby_places` already take. It is
    Now's rather than Matches' because **the match is unchanged by an offer**:
    no rung reads one, so routing it through `Match` would bump ADR-0034's
    version and invalidate the scoring-context cache on every dispatch.
    """
    return SqlAlchemyOffers(session)


def build_cascade_waves(session: AsyncSession) -> CascadeWaves:
    """The dispatch queue: two rows per hole, and when each may run.

    Its own queue and not `next_wake`, because a dispatch is not a boundary the
    ladder reads — nothing about the match resolves differently at vacancy + 10
    minutes, and ADR-0076 forbids a threshold in the timekeeper by name.
    """
    return SqlAlchemyCascadeWaves(session)


def build_rated_players(events: DomainEventStore) -> RatedPlayers:
    """Everybody holding a rating at one sport — the pool's population.

    The event store rather than the rating repository, and that is the whole of
    why this port exists: a rating stream's id **is** `(player, sport)`, which
    makes every other rating read one lookup and makes *who holds one*
    unanswerable from an id. The opening events are the only end it can be asked
    from.
    """
    return RatedPlayersFromRatingStreams(events)


def build_club_regulars(matches: MatchRepository) -> ClubRegulars:
    """Who has played at one club — rung 5, as far as the product can see it."""
    return ClubRegularsFromMatches(matches)


def build_open_cascade(
    *, waves: CascadeWaves, contexts: CityMatches
) -> OpenCascade:
    """Put a hole's two dispatches on the queue, with the quiet hours applied.

    It takes `CityMatches` for the **club's zone**: ADR-0052 holds delivery to
    08:00 local, and the player the platform cannot locate has no zone of her
    own to hold it to (`Raketa02/Raketa#102`).
    """
    return OpenCascade(waves=waves, contexts=contexts)


def build_run_cascade(
    *,
    waves: CascadeWaves,
    offers: Offers,
    contexts: CityMatches,
    players: RatedPlayers,
    regulars: ClubRegulars,
    commitments: Commitments,
    ratings: Ratings,
    standby: StandbyQueue,
    scorer: MatchScorer,
    uow: UnitOfWork,
    clock: Clock,
) -> RunCascade:
    """One dispatch: assemble the pool, rank it, write the offers.

    Every rung is a port and none of them is a session, so *which store answers
    which rung* is visible here in one place — including the three that answer
    nothing, which are absent because a dark rung reads no store at all rather
    than reading an empty one.
    """
    return RunCascade(
        waves=waves,
        offers=offers,
        contexts=contexts,
        players=players,
        regulars=regulars,
        commitments=commitments,
        ratings=ratings,
        standby=standby,
        scorer=scorer,
        uow=uow,
        clock=clock,
    )


def build_cascade_batch(
    *, waves: CascadeWaves, run: RunCascade, uow: UnitOfWork, clock: Clock
) -> CascadeBatch:
    """Every dispatch due at this instant, run once each.

    A batch on the event worker beside the outbox drain and the match wakes, for
    their reason: one indexed query, a bounded slice of work, and whatever is
    left is still due next tick.
    """
    return CascadeBatch(waves=waves, run=run, uow=uow, clock=clock)


def build_cascade_tick(
    *,
    session: AsyncSession,
    event_runtime: EventRuntime,
    contexts: ScoringContexts,
    clock: Clock,
) -> CascadeBatch:
    """ADR-0061's dispatch queue, wired from the same factories a request gets.

    The counterpart of `build_match_wake_batch`, and it takes an
    `EventRuntime` for the same reason: the match repository every caller gets
    is built with a publisher, so a cascade that ever reached a write would
    reach the outbox the way a tap does. It does not — nothing here mutates a
    match — and building it the ordinary way is what keeps that an observation
    rather than a worker-only path.

    Every rung is a port, and the three dark ones are absent because a dark rung
    reads no store rather than reading an empty one.

    The scoring-context cache is **handed in** rather than made here, because it
    is the one adapter in this app whose lifetime is the application's: a fresh
    one per tick would re-read every club and replay every seated rating for a
    match a screen had just paid for. Keyed `matchId : recordVersion`, so
    sharing it across the request path and the tick cannot serve either a stale
    answer.
    """

    events = event_runtime.create_publisher_for(session=session)
    event_store = build_domain_event_store(session, runtime=event_runtime)
    uow = build_unit_of_work(session)
    matches = build_match_repository(session, events=events, clock=clock)
    ratings = build_ratings(
        build_skill_rating_repository(event_store=event_store, events=events)
    )
    waves = build_cascade_waves(session)
    return build_cascade_batch(
        waves=waves,
        run=build_run_cascade(
            waves=waves,
            offers=build_offers(session),
            contexts=build_city_matches(
                matches=matches,
                clubs=build_club_repository(session),
                reservations=build_reservation_repository(session),
                ratings=ratings,
                contexts=contexts,
            ),
            players=build_rated_players(event_store),
            regulars=build_club_regulars(matches),
            commitments=build_commitments(matches),
            ratings=ratings,
            standby=build_standby(
                matches=matches, standby=build_match_standby_places(session)
            ),
            scorer=build_match_scorer(),
            uow=uow,
            clock=clock,
        ),
        uow=uow,
        clock=clock,
    )


def build_results(*, matches: MatchRepository) -> Results:
    """The result conversation's two writes (ADR-0074).

    One port rather than a session, like every builder around it. **No hold
    ladder beside it**, unlike `build_departures`: nothing about a result moves a
    seat, so no tier can be entered or left and there is no court to give back.

    **It does not commit.** The score, its announcement and the recomposed answer
    close together, and that is the use case's transaction to close.
    """
    return ResultsThroughMatches(matches=matches)


def build_read_result(*, enrolled: EnrolledMatches, clock: Clock) -> ReadResult:
    """What this match's result conversation is doing, for this viewer."""
    return ReadResult(enrolled=enrolled, clock=clock)


def build_propose_result(
    *,
    enrolled: EnrolledMatches,
    results: Results,
    uow: UnitOfWork,
    clock: Clock,
) -> ProposeResult:
    """Put a score up, and hand back this screen's answer **and** Now's update."""
    return ProposeResult(
        enrolled=enrolled, results=results, uow=uow, clock=clock
    )


def build_accept_result(
    *,
    enrolled: EnrolledMatches,
    results: Results,
    uow: UnitOfWork,
    clock: Clock,
) -> AcceptResult:
    """Agree with the score on the table, and hand Now its update."""
    return AcceptResult(
        enrolled=enrolled, results=results, uow=uow, clock=clock
    )


def build_ratings(ratings: SkillRatingRepository) -> Ratings:
    """One player's rating at one sport, in the **engines'** vocabulary.

    A second adapter over the same repository as `build_levels`, and deliberately
    not one object answering both ports the way `build_arrivals` does: those two
    are the same eligibility asked at two depths, where these two are two
    different facts — a card's Level and its quiet marker against an engine's
    Level, Uncertainty and Confidence. One object would be a class with two
    unrelated methods that happen to share a constructor.
    """
    return RatingsFromSkillRatings(ratings=ratings)


def build_city_matches(
    *,
    matches: MatchRepository,
    clubs: ClubRepository,
    reservations: ReservationRepository,
    ratings: Ratings,
    contexts: ScoringContexts,
) -> CityMatches:
    """Every suggestible match in the window, and what scoring one needs.

    Five **ports** rather than a session, on the precedent `build_arrivals` set.
    One is Now's own `Ratings` and not the rating repository, so the one crossing
    from a stored float μ into the engines' exact ratio happens in a single place
    for the whole screen.

    The context cache is a collaborator here rather than a decorator above the
    port, because its key is a fact about the **match**: assembling every context
    and then discarding it for the copy already held is a cache that saves
    nothing. ADR-0068 puts the new-arrivals cache the other way round for the
    complementary reason — its key carries the viewer's city.
    """
    return CityMatchesFromMatches(
        matches=matches,
        clubs=clubs,
        reservations=reservations,
        ratings=ratings,
        contexts=contexts,
    )


def build_commitments(matches: MatchRepository) -> Commitments:
    """What the viewer is already doing, as three columns and nothing more."""
    return CommitmentsFromMatches(matches)


def build_standby(
    *, matches: MatchRepository, standby: MatchStandbyPlaces
) -> StandbyThroughMatches:
    """Which matches the viewer is queued for, and the write that leaves one.

    One object answering **two** ports, on the precedent `build_arrivals` set:
    they are one question asked in two directions, and a second class would be
    a second file that knows a standby place is a row in the Matches context.
    They stay two ports because their readers differ — `ComposeShelves` takes
    the read alone.

    **The store landed.**

    This function is the one line ADR-0087's predecessor promised would change:
    it used to take nothing and answer the empty set for everybody, because
    standby had no table anywhere in the product. The rule above it —
    `NotOnStandby`, one of the funnel's eight — has been written, evaluated and
    tested the whole time, which is why landing the store cost a constructor
    call rather than a pipeline change (`Raketa02/Raketa#81`).

    Two ports rather than a session, like every builder around it. The match
    repository is here to turn an unknown id into a 404 on the write and for
    nothing else.
    """
    return StandbyThroughMatches(matches=matches, standby=standby)


def build_match_standby_places(session: AsyncSession) -> MatchStandbyPlaces:
    """The queue itself: one table with the pair as its primary key.

    A session rather than ports, because it *is* one table. It is deliberately
    not part of the `Match` aggregate — a join moves no state anybody contends
    for, and routing it through the aggregate would bump ADR-0034's version
    column and invalidate the scoring-context cache every time somebody queued.
    """
    return SqlAlchemyStandbyPlaces(session)


def build_leave_standby(
    *,
    enrolled: EnrolledMatches,
    standby: Standby,
    uow: UnitOfWork,
    clock: Clock,
) -> LeaveStandby:
    """ADR-0087's write: leave the queue, and hand Now the one card that changed.

    No command log, unlike the departure beside it. ADR-0030's log is for
    *destructive* commands and this one is idempotent by its own nature, so a
    replay has nothing to hand back that a fresh run would not compute.
    """
    return LeaveStandby(enrolled=enrolled, standby=standby, uow=uow, clock=clock)


def build_join_standby(
    *,
    matches: MatchRepository,
    standby: MatchStandbyPlaces,
    clock: Clock,
) -> JoinStandby:
    """The write with no route, because v1 has no surface that joins a queue.

    The waitlist toggle is a match-screen control and the match screen is out of
    scope, so the only caller today is the seed catalog — which executes use
    cases and never SQL, so a seeded standby place has to be written by the code
    a request would run.
    """
    return JoinStandby(matches=matches, standby=standby, clock=clock)


def build_scoring_contexts() -> ScoringContexts:
    """The match scoring context cache — **not** per request, like the other one.

    Its whole value is being shared across viewers, so its lifetime is the
    application's. It takes no clock, because it has no TTL: ADR-0068 keys it
    `matchId : recordVersion`, so it is never stale and the invalidation is
    already in the key.
    """
    return InMemoryScoringContexts()


def build_match_scorer() -> MatchScorer:
    """Pairing, then Match Fit, on the two **abstractions** and never a version.

    The one place either engine is named, which is what makes swapping
    `matchfit/v1` for a later lineage — or for an implementation behind HTTP — a
    line here rather than an edit in the application layer (ADR-0015). The
    caller runs Pairing and hands the analysis to Match Fit, so the score and the
    aimed-at Level printed beside it come from one analysis by construction
    (ADR-0026).
    """
    return MatchScorer(pairing=PairingEngineV1(), matchfit=MatchFitEngineV1())


def build_compose_shelves(
    *,
    city: CityMatches,
    commitments: Commitments,
    standby: StandbyPlaces,
    ratings: Ratings,
    scorer: MatchScorer,
) -> ComposeShelves:
    """Shelves 1 and 2 — the ranked funnel, and the only judged part of Now."""
    return ComposeShelves(
        city=city,
        commitments=commitments,
        standby=standby,
        ratings=ratings,
        scorer=scorer,
    )


# --------------------------------------------------------------------------
# Money
# --------------------------------------------------------------------------


def build_ledger_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> LedgerRepository:
    """Per unit of work, for the same reason the rating repository is.

    It recovers a stream's version rather than being told it, so two use cases
    sharing one transaction have to share one of these — otherwise the second
    appends at a version the first has already passed. Under FastAPI that comes
    free from per-request dependency caching; a seed run or a worker builds it
    once and passes it on.
    """
    return EventSourcedLedgerRepository(event_store=event_store, events=events)


def build_seats(
    *,
    matches: MatchRepository,
    holds: ResolveCourtHold,
    reservations: ReservationRepository,
) -> Seats:
    """Money's one question to another context: *give her the seat this paid for.*

    Takes three **ports and a use case** rather than a session, so the seat
    write, the hold ladder and the court behind it are the same ones every other
    caller gets. In particular ``holds`` is passed in rather than built here:
    ADR-0031 makes ``ResolveCourtHold`` the only thing allowed to move
    ``held_since``, and a second instance would be a second one of those.

    It commits nothing. The transaction that carries the seat, the reservation
    and both outbox rows belongs to ``money.PayForASeat`` (ADR-0035,
    `Raketa02/Raketa#70`).
    """

    return SeatsThroughMatches(matches=matches, holds=holds, reservations=reservations)
