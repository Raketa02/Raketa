"""When Now's ports are built, and how long they live. Never *what* is built.

Every construction happens in ``app/bootstrap/composition.py``; these callables
only declare the lifetime, exactly as every other module's do. A test walks these
files and reddens if one imports an adapter, because the failure mode is one line
of convenience inside a ``Depends`` callable and nothing about a green suite would
look different afterwards.

**Two of these lifetimes are not the request's**, and they are the only two in
the app: both of Now's caches are shared across viewers, so a per-request
instance would be a cache that is cold on every request. They are built once in
``create_app`` and read off ``app.state`` here, which is the same shape the event
runtime already uses. The new-arrivals cache is shared by everybody in a city
looking at one sport; the scoring context cache is shared by everybody looking at
one match, and it has no TTL at all because its key carries the record's
version.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    UnitOfWorkDep,
    UserRepositoryDep,
)
from app.application.ports import CommandLog
from app.bootstrap.composition import (
    build_arrivals,
    build_assessment_repository,
    build_cascade_waves,
    build_city_matches,
    build_open_cascade,
    build_push_devices,
    build_register_device,
    build_club_repository,
    build_command_log,
    build_commitments,
    build_claims,
    build_compose_enrolled,
    build_compose_new_arrivals,
    build_compose_offers,
    build_compose_shelves,
    build_court_holds,
    build_departures,
    build_enrolled_matches,
    build_leave_standby,
    build_ledger_repository,
    build_levels,
    build_make_departure,
    build_match_repository,
    build_match_scorer,
    build_match_standby_places,
    build_offered_seats,
    build_offers,
    build_parked_runs,
    build_rated_sports,
    build_accept_result,
    build_propose_result,
    build_ratings,
    build_read_departure,
    build_read_result,
    build_results,
    build_reservation_repository,
    build_seat_claims,
    build_skill_rating_repository,
    build_standby,
    build_take_the_seat,
)
from app.modules.courts.application.claim_court import ClaimCourt
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.now.application.compose_enrolled import ComposeEnrolled
from app.modules.now.application.compose_now import ComposeNow
from app.modules.now.application.compose_offers import ComposeOffers
from app.modules.now.application.compose_shelves import ComposeShelves
from app.modules.now.application.departure import MakeDeparture, ReadDeparture
from app.modules.now.application.result import (
    AcceptResult,
    ProposeResult,
    ReadResult,
)
from app.modules.now.application.new_arrivals import ComposeNewArrivals
from app.modules.now.application.cascade import OpenCascade
from app.modules.now.application.seat import TakeTheSeat
from app.modules.now.application.push import RegisterDevice
from app.modules.now.application.standby import LeaveStandby
from app.modules.now.domain.ports import (
    ArrivalSets,
    Claims,
    Departures,
    EnrolledMatches,
    Levels,
    OfferedSeats,
    ParkedRuns,
    PushDevices,
    RatedSports,
    Ratings,
    Results,
    ScoringContexts,
    Standby,
)
from app.modules.rating.domain.ports import (
    AssessmentRepository,
    SkillRatingRepository,
)


def get_skill_ratings(
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
) -> SkillRatingRepository:
    # Declared here rather than borrowed from the rating module's own dependency
    # file: one module reaching into another's presentation layer is a coupling
    # neither of them asked for, and both are three lines over the same factory.
    #
    # One per request, and that matters here rather than being tidy: two of Now's
    # ports read ratings, and FastAPI caches this callable for the request, so
    # both are answered by the same replay cache instead of two.
    return build_skill_rating_repository(event_store=event_store, events=events)


SkillRatingsDep = Annotated[SkillRatingRepository, Depends(get_skill_ratings)]


def get_rated_sports(ratings: SkillRatingsDep) -> RatedSports:
    return build_rated_sports(ratings)


RatedSportsDep = Annotated[RatedSports, Depends(get_rated_sports)]


def get_assessments(
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
) -> AssessmentRepository:
    # Declared here rather than borrowed from the rating module's own dependency
    # file, on the same rule `get_skill_ratings` above states: one module reaching
    # into another's presentation layer is a coupling neither asked for.
    return build_assessment_repository(event_store=event_store, events=events)


AssessmentsDep = Annotated[AssessmentRepository, Depends(get_assessments)]


def get_parked_runs(assessments: AssessmentsDep) -> ParkedRuns:
    return build_parked_runs(assessments)


ParkedRunsDep = Annotated[ParkedRuns, Depends(get_parked_runs)]


def get_levels(ratings: SkillRatingsDep) -> Levels:
    return build_levels(ratings)


LevelsDep = Annotated[Levels, Depends(get_levels)]


def get_arrival_sets(request: Request) -> ArrivalSets:
    """The one adapter in this app whose lifetime is the **application's**.

    Read off ``app.state`` rather than constructed here, and rather than held in
    a module-level singleton: the second shape survives between two tests, so a
    set written against one test's database would answer a question asked of
    another's — invisible, and exactly the kind of green suite this tree spends
    itself avoiding. ``create_app`` builds one per application, so a test that
    builds an app gets a cold cache.
    """

    sets: ArrivalSets = request.app.state.arrival_sets
    return sets


ArrivalSetsDep = Annotated[ArrivalSets, Depends(get_arrival_sets)]


def get_new_arrivals(
    db: DbSession,
    users: UserRepositoryDep,
    ratings: SkillRatingsDep,
    levels: LevelsDep,
    sets: ArrivalSetsDep,
) -> ComposeNewArrivals:
    arrivals = build_arrivals(
        users=users, ratings=ratings, clubs=build_club_repository(db)
    )
    # One object, two ports: the cache stores what one of them returns and could
    # not store what the other does, which is the split ADR-0068 draws.
    return build_compose_new_arrivals(
        arrivals=arrivals, rows=arrivals, levels=levels, sets=sets
    )


NewArrivalsDep = Annotated[ComposeNewArrivals, Depends(get_new_arrivals)]


def get_enrolled_matches(
    db: DbSession,
    users: UserRepositoryDep,
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
    clock: ClockDep,
) -> EnrolledMatches:
    """The enrolled strip's seven reads, all of them per request.

    The match repository is built with the publisher and the clock every other
    caller gets. It is a **read** on the composed screen — nothing a `GET /now`
    does can reach the outbox through it — and the same port answers the one
    match an action off Now is about, so the strip and the departure route can
    never describe a match differently.

    The queue is the sixth, and it is read here rather than composed beside the
    strip because a standby place is a fact about **this pair** exactly as a
    seat is: the kernel takes both through one `Viewer`, so assembling them in
    two places would be assembling the viewer twice.

    The seat claim is the seventh, and it is the same lookup `ClaimSeat` takes:
    one live claim per player across the platform, so it widens the strip by one
    match rather than by a set (`Raketa02/Raketa#83`).
    """

    return build_enrolled_matches(
        matches=build_match_repository(db, events=events, clock=clock),
        standby=build_match_standby_places(db),
        claims=build_seat_claims(db),
        clubs=build_club_repository(db),
        reservations=build_reservation_repository(db),
        users=users,
        ledgers=build_ledger_repository(event_store=event_store, events=events),
    )


EnrolledMatchesDep = Annotated[EnrolledMatches, Depends(get_enrolled_matches)]


def get_compose_enrolled(enrolled: EnrolledMatchesDep) -> ComposeEnrolled:
    return build_compose_enrolled(enrolled=enrolled)


EnrolledDep = Annotated[ComposeEnrolled, Depends(get_compose_enrolled)]


def get_departures(
    db: DbSession, events: EventPublisherDep, uow: UnitOfWorkDep, clock: ClockDep
) -> Departures:
    """The one write behind an action off Now, and the hold ladder beside it.

    The ladder is wired exactly as the timekeeper's is — the same
    `ResolveCourtHold` over the same repository — because *a wake is a look* and
    a tap is a look too: one wiring of the ladder, or a rule true on one path
    and false on the other. A departure leaves a hold tier, so this is the ask
    that gives a court back.
    """

    matches = build_match_repository(db, events=events, clock=clock)
    reservations = build_reservation_repository(db)
    holds = build_court_holds(
        ClaimCourt(build_club_repository(db), reservations, uow), reservations
    )
    return build_departures(
        matches=matches, holds=ResolveCourtHold(matches, holds, uow, clock)
    )


DeparturesDep = Annotated[Departures, Depends(get_departures)]


def get_standby(db: DbSession, events: EventPublisherDep, clock: ClockDep) -> Standby:
    """ADR-0087's write, and the read the shelves already had.

    One adapter behind two ports: the composer takes the read alone, because a
    composer holding an object that can delete a player's queue place is a
    composer one autocomplete away from doing it.
    """

    return build_standby(
        matches=build_match_repository(db, events=events, clock=clock),
        standby=build_match_standby_places(db),
    )


StandbyDep = Annotated[Standby, Depends(get_standby)]


def get_leave_standby(
    enrolled: EnrolledMatchesDep,
    standby: StandbyDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> LeaveStandby:
    return build_leave_standby(
        enrolled=enrolled, standby=standby, uow=uow, clock=clock
    )


LeaveStandbyDep = Annotated[LeaveStandby, Depends(get_leave_standby)]


def get_command_log(db: DbSession) -> CommandLog:
    return build_command_log(db)


CommandLogDep = Annotated[CommandLog, Depends(get_command_log)]


def get_read_departure(enrolled: EnrolledMatchesDep, clock: ClockDep) -> ReadDeparture:
    return build_read_departure(enrolled=enrolled, clock=clock)


ReadDepartureDep = Annotated[ReadDeparture, Depends(get_read_departure)]


def get_open_cascade(
    db: DbSession,
    ratings: RatingsDep,
    contexts: ScoringContextsDep,
    events: EventPublisherDep,
    clock: ClockDep,
) -> OpenCascade:
    """The two rows a departure writes so the seat reaches somebody.

    It builds a ``CityMatches`` of its own, and that is the cost of the club's
    **zone**: ADR-0052 holds delivery to 08:00 local, and nothing else on this
    route needs a club at all. The scoring-context cache is shared with the
    compose path, so a hole opening moments after a screen was drawn pays
    nothing for it.
    """

    return build_open_cascade(
        waves=build_cascade_waves(db),
        contexts=build_city_matches(
            matches=build_match_repository(db, events=events, clock=clock),
            clubs=build_club_repository(db),
            reservations=build_reservation_repository(db),
            ratings=ratings,
            contexts=contexts,
        ),
    )


OpenCascadeDep = Annotated[OpenCascade, Depends(get_open_cascade)]


def get_make_departure(
    enrolled: EnrolledMatchesDep,
    departures: DeparturesDep,
    cascade: OpenCascadeDep,
    log: CommandLogDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> MakeDeparture:
    return build_make_departure(
        enrolled=enrolled,
        departures=departures,
        cascade=cascade,
        log=log,
        uow=uow,
        clock=clock,
    )


MakeDepartureDep = Annotated[MakeDeparture, Depends(get_make_departure)]


def get_results(db: DbSession, events: EventPublisherDep, clock: ClockDep) -> Results:
    """The result conversation's two writes, over the repository every caller gets.

    **No hold ladder here**, which is the one difference from `get_departures`:
    a score moves no seat, so no tier can be entered or left and there is no
    court to give back. Wiring one in would be a look with nothing to find, and
    the kind of copied line that later reads as a rule.
    """

    return build_results(
        matches=build_match_repository(db, events=events, clock=clock)
    )


ResultsDep = Annotated[Results, Depends(get_results)]


def get_read_result(enrolled: EnrolledMatchesDep, clock: ClockDep) -> ReadResult:
    return build_read_result(enrolled=enrolled, clock=clock)


ReadResultDep = Annotated[ReadResult, Depends(get_read_result)]


def get_propose_result(
    enrolled: EnrolledMatchesDep,
    results: ResultsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> ProposeResult:
    return build_propose_result(
        enrolled=enrolled, results=results, uow=uow, clock=clock
    )


ProposeResultDep = Annotated[ProposeResult, Depends(get_propose_result)]


def get_accept_result(
    enrolled: EnrolledMatchesDep,
    results: ResultsDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> AcceptResult:
    return build_accept_result(
        enrolled=enrolled, results=results, uow=uow, clock=clock
    )


AcceptResultDep = Annotated[AcceptResult, Depends(get_accept_result)]


def get_ratings(ratings: SkillRatingsDep) -> Ratings:
    return build_ratings(ratings)


RatingsDep = Annotated[Ratings, Depends(get_ratings)]


def get_scoring_contexts(request: Request) -> ScoringContexts:
    """The second adapter whose lifetime is the **application's**.

    Read off ``app.state`` for the same reason ``get_arrival_sets`` is: a
    module-level singleton would carry one test's contexts into another's
    database. It differs from that one in having no TTL — its key is
    ``matchId : recordVersion``, so an entry cannot be stale, and there is
    nothing for a clock to decide.
    """

    contexts: ScoringContexts = request.app.state.scoring_contexts
    return contexts


ScoringContextsDep = Annotated[ScoringContexts, Depends(get_scoring_contexts)]


def get_compose_shelves(
    db: DbSession,
    ratings: RatingsDep,
    contexts: ScoringContextsDep,
    events: EventPublisherDep,
    clock: ClockDep,
) -> ComposeShelves:
    """The ranked funnel's four reads, plus the shared cache and two engines.

    The match repository is built with the publisher and the clock every other
    caller gets, and it is a **read** here: Now writes nothing, so nothing this
    request does can reach the outbox through it. It is built once and handed to
    both ``CityMatches`` and ``Commitments``, which ask it two different
    questions — the city's matches and this player's — so they share one replay
    rather than opening two.
    """

    matches = build_match_repository(db, events=events, clock=clock)
    return build_compose_shelves(
        city=build_city_matches(
            matches=matches,
            clubs=build_club_repository(db),
            reservations=build_reservation_repository(db),
            ratings=ratings,
            contexts=contexts,
        ),
        commitments=build_commitments(matches),
        standby=build_standby(
            matches=matches, standby=build_match_standby_places(db)
        ),
        ratings=ratings,
        scorer=build_match_scorer(),
    )


ShelvesDep = Annotated[ComposeShelves, Depends(get_compose_shelves)]


def get_offered_seats(
    db: DbSession, events: EventPublisherDep, clock: ClockDep
) -> OfferedSeats:
    """The offers region's four reads, all of them per request.

    The offers store is Now's own table and the other three belong to Matches,
    Clubs and Courts. The match repository is built with the publisher and the
    clock every other caller gets: this is a **read** on the composed screen, and
    nothing a `GET /now` does can reach the outbox through it.
    """

    return build_offered_seats(
        offers=build_offers(db),
        matches=build_match_repository(db, events=events, clock=clock),
        clubs=build_club_repository(db),
        reservations=build_reservation_repository(db),
    )


OfferedSeatsDep = Annotated[OfferedSeats, Depends(get_offered_seats)]


def get_compose_offers(offered: OfferedSeatsDep) -> ComposeOffers:
    return build_compose_offers(offered=offered)


OffersDep = Annotated[ComposeOffers, Depends(get_compose_offers)]


def get_claims(
    db: DbSession, events: EventPublisherDep, uow: UnitOfWorkDep, clock: ClockDep
) -> Claims:
    """Now's second write, and the hold ladder beside it.

    The ladder is wired exactly as the departure's is — the same
    `ResolveCourtHold` over the same repository — because every Matches write
    asks it before the save, and a claim being the one that does not is how a
    rule comes to be true on one path and false on another.
    """

    matches = build_match_repository(db, events=events, clock=clock)
    reservations = build_reservation_repository(db)
    holds = build_court_holds(
        ClaimCourt(build_club_repository(db), reservations, uow), reservations
    )
    return build_claims(
        matches=matches,
        claims=build_seat_claims(db),
        holds=ResolveCourtHold(matches, holds, uow, clock),
    )


ClaimsDep = Annotated[Claims, Depends(get_claims)]


def get_take_the_seat(
    claims: ClaimsDep,
    offered: OfferedSeatsDep,
    enrolled: EnrolledMatchesDep,
    offers: OffersDep,
    strip: EnrolledDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> TakeTheSeat:
    return build_take_the_seat(
        claims=claims,
        offered=offered,
        enrolled=enrolled,
        offers=offers,
        strip=strip,
        uow=uow,
        clock=clock,
    )


TakeTheSeatDep = Annotated[TakeTheSeat, Depends(get_take_the_seat)]


def get_compose_now(
    rated_sports: RatedSportsDep,
    parked_runs: ParkedRunsDep,
    new_arrivals: NewArrivalsDep,
    shelves: ShelvesDep,
    enrolled: EnrolledDep,
    offers: OffersDep,
    clock: ClockDep,
) -> ComposeNow:
    return ComposeNow(
        rated_sports=rated_sports,
        parked_runs=parked_runs,
        new_arrivals=new_arrivals,
        shelves=shelves,
        enrolled=enrolled,
        offers=offers,
        clock=clock,
    )


ComposeNowDep = Annotated[ComposeNow, Depends(get_compose_now)]


def get_push_devices(db: DbSession) -> PushDevices:
    """Where a player's phones are. Request-scoped, like every other store."""

    return build_push_devices(db)


PushDevicesDep = Annotated[PushDevices, Depends(get_push_devices)]


def get_register_device(
    devices: PushDevicesDep, uow: UnitOfWorkDep, clock: ClockDep
) -> RegisterDevice:
    """*Reach me here.* The channel's only route.

    No sender and no lines: registering a phone sends nothing. The first message
    it can receive is the next one a dispatch owes her, which is the queue's
    business and not this request's.
    """

    return build_register_device(devices=devices, uow=uow, clock=clock)


RegisterDeviceDep = Annotated[RegisterDevice, Depends(get_register_device)]
