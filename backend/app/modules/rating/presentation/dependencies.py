from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DomainEventStoreDep,
    EventPublisherDep,
    UnitOfWorkDep,
)
from app.engines.assessment import AssessmentEngine
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.modules.rating.application.abandon_assessment import AbandonAssessment
from app.modules.rating.application.create_assessment import CreateAssessment
from app.modules.rating.application.find_in_progress_assessment import (
    FindInProgressAssessment,
    ListInProgressAssessments,
)
from app.modules.rating.application.get_assessment import GetAssessment
from app.modules.rating.application.list_ratings import ListPlayerRatings
from app.modules.rating.application.submit_answer import SubmitAnswer
from app.modules.rating.domain.ports import AssessmentRepository
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    EventSourcedAssessmentRepository,
)


def get_assessment_engine() -> AssessmentEngine:
    # The concrete engine version is chosen here, at the boundary; the use cases
    # depend only on the ``AssessmentEngine`` abstraction, so a version swap is a
    # one-line change.
    return RacketSkillEngineV3()


AssessmentEngineDep = Annotated[AssessmentEngine, Depends(get_assessment_engine)]


def get_assessment_repository(
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
) -> AssessmentRepository:
    # Per request, like the event store and publisher it is built from. The
    # repository remembers the versions it loaded, and one request's versions
    # must never answer for another's.
    return EventSourcedAssessmentRepository(event_store=event_store, events=events)


AssessmentRepositoryDep = Annotated[
    AssessmentRepository, Depends(get_assessment_repository)
]


def get_create_assessment(
    engine: AssessmentEngineDep,
    event_store: DomainEventStoreDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
    events: EventPublisherDep,
) -> CreateAssessment:
    return CreateAssessment(
        engine=engine,
        event_store=event_store,
        uow=uow,
        clock=clock,
        events=events,
    )


CreateAssessmentDep = Annotated[CreateAssessment, Depends(get_create_assessment)]


def get_submit_answer(
    engine: AssessmentEngineDep,
    event_store: DomainEventStoreDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
    events: EventPublisherDep,
) -> SubmitAnswer:
    return SubmitAnswer(
        engine=engine,
        event_store=event_store,
        uow=uow,
        clock=clock,
        events=events,
    )


SubmitAnswerDep = Annotated[SubmitAnswer, Depends(get_submit_answer)]


def get_get_assessment(
    engine: AssessmentEngineDep,
    event_store: DomainEventStoreDep,
) -> GetAssessment:
    return GetAssessment(engine=engine, event_store=event_store)


GetAssessmentDep = Annotated[GetAssessment, Depends(get_get_assessment)]


def get_find_in_progress_assessment(
    engine: AssessmentEngineDep,
    event_store: DomainEventStoreDep,
) -> FindInProgressAssessment:
    return FindInProgressAssessment(engine=engine, event_store=event_store)


FindInProgressAssessmentDep = Annotated[
    FindInProgressAssessment, Depends(get_find_in_progress_assessment)
]


def get_list_in_progress_assessments(
    event_store: DomainEventStoreDep,
) -> ListInProgressAssessments:
    # No engine: the collection reports which runs are unfinished, not what they
    # are asking. Reproducing four outstanding questions to answer "none" would
    # be work nobody reads.
    return ListInProgressAssessments(event_store=event_store)


ListInProgressAssessmentsDep = Annotated[
    ListInProgressAssessments, Depends(get_list_in_progress_assessments)
]


def get_abandon_assessment(
    assessments: AssessmentRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> AbandonAssessment:
    return AbandonAssessment(assessments=assessments, uow=uow, clock=clock)


AbandonAssessmentDep = Annotated[AbandonAssessment, Depends(get_abandon_assessment)]


def get_list_player_ratings(event_store: DomainEventStoreDep) -> ListPlayerRatings:
    # No engine: a stored rating is replayed, never recomputed. Its numbers are
    # the ones the player was shown, whatever the engine has since become.
    return ListPlayerRatings(event_store=event_store)


ListPlayerRatingsDep = Annotated[ListPlayerRatings, Depends(get_list_player_ratings)]
