"""When Now's ports are built, and how long they live. Never *what* is built.

Every construction happens in ``app/bootstrap/composition.py``; these callables
only declare the lifetime, exactly as every other module's do. A test walks these
files and reddens if one imports an adapter, because the failure mode is one line
of convenience inside a ``Depends`` callable and nothing about a green suite would
look different afterwards.

**One of these lifetimes is not the request's**, and it is the only one in the
app: the new-arrivals cache is shared by everybody in a city looking at one
sport, so a per-request instance would be a cache that is cold on every request
— an object with a TTL and no hits. It is built once in ``create_app`` and read
off ``app.state`` here, which is the same shape the event runtime already uses.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    UserRepositoryDep,
)
from app.bootstrap.composition import (
    build_arrivals,
    build_assessment_repository,
    build_club_repository,
    build_compose_enrolled,
    build_compose_new_arrivals,
    build_enrolled_matches,
    build_ledger_repository,
    build_levels,
    build_match_repository,
    build_parked_runs,
    build_rated_sports,
    build_reservation_repository,
    build_skill_rating_repository,
)
from app.modules.now.application.compose_enrolled import ComposeEnrolled
from app.modules.now.application.compose_now import ComposeNow
from app.modules.now.application.new_arrivals import ComposeNewArrivals
from app.modules.now.domain.ports import ArrivalSets, Levels, ParkedRuns, RatedSports
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


def get_compose_enrolled(
    db: DbSession,
    users: UserRepositoryDep,
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
    clock: ClockDep,
) -> ComposeEnrolled:
    """The enrolled strip's five reads, all of them per request.

    The match repository is built with the publisher and the clock every other
    caller gets, and it is a **read** here — Now writes nothing, so nothing this
    request does can reach the outbox through it.
    """

    return build_compose_enrolled(
        enrolled=build_enrolled_matches(
            matches=build_match_repository(db, events=events, clock=clock),
            clubs=build_club_repository(db),
            reservations=build_reservation_repository(db),
            users=users,
            ledgers=build_ledger_repository(event_store=event_store, events=events),
        )
    )


EnrolledDep = Annotated[ComposeEnrolled, Depends(get_compose_enrolled)]


def get_compose_now(
    rated_sports: RatedSportsDep,
    parked_runs: ParkedRunsDep,
    new_arrivals: NewArrivalsDep,
    enrolled: EnrolledDep,
    clock: ClockDep,
) -> ComposeNow:
    return ComposeNow(
        rated_sports=rated_sports,
        parked_runs=parked_runs,
        new_arrivals=new_arrivals,
        enrolled=enrolled,
        clock=clock,
    )


ComposeNowDep = Annotated[ComposeNow, Depends(get_compose_now)]
