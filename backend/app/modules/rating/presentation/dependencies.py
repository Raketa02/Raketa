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
from app.modules.rating.domain.ports import AssessmentRepository, SkillRatingRepository
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    EventSourcedAssessmentRepository,
)
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    EventSourcedSkillRatingRepository,
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


def get_skill_rating_repository(
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
) -> SkillRatingRepository:
    # Per request, for the same reason the assessment's is: it remembers the
    # versions it read, and one request's versions must never answer for
    # another's.
    return EventSourcedSkillRatingRepository(event_store=event_store, events=events)


SkillRatingRepositoryDep = Annotated[
    SkillRatingRepository, Depends(get_skill_rating_repository)
]


def get_create_assessment(
    engine: AssessmentEngineDep,
    assessments: AssessmentRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> CreateAssessment:
    return CreateAssessment(
        engine=engine,
        assessments=assessments,
        uow=uow,
        clock=clock,
    )


CreateAssessmentDep = Annotated[CreateAssessment, Depends(get_create_assessment)]


def get_submit_answer(
    engine: AssessmentEngineDep,
    assessments: AssessmentRepositoryDep,
    ratings: SkillRatingRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SubmitAnswer:
    # Two repositories and one unit of work: completion writes both streams
    # inside one transaction, and only the transaction is this use case's.
    return SubmitAnswer(
        engine=engine,
        assessments=assessments,
        ratings=ratings,
        uow=uow,
        clock=clock,
    )


SubmitAnswerDep = Annotated[SubmitAnswer, Depends(get_submit_answer)]


def get_get_assessment(
    engine: AssessmentEngineDep,
    assessments: AssessmentRepositoryDep,
) -> GetAssessment:
    return GetAssessment(engine=engine, assessments=assessments)


GetAssessmentDep = Annotated[GetAssessment, Depends(get_get_assessment)]


def get_find_in_progress_assessment(
    engine: AssessmentEngineDep,
    assessments: AssessmentRepositoryDep,
) -> FindInProgressAssessment:
    return FindInProgressAssessment(engine=engine, assessments=assessments)


FindInProgressAssessmentDep = Annotated[
    FindInProgressAssessment, Depends(get_find_in_progress_assessment)
]


def get_list_in_progress_assessments(
    assessments: AssessmentRepositoryDep,
) -> ListInProgressAssessments:
    # No engine: the collection reports which runs are unfinished, not what they
    # are asking. Reproducing four outstanding questions to answer "none" would
    # be work nobody reads.
    return ListInProgressAssessments(assessments=assessments)


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


def get_list_player_ratings(ratings: SkillRatingRepositoryDep) -> ListPlayerRatings:
    # No engine: a stored rating is replayed, never recomputed. Its numbers are
    # the ones the player was shown, whatever the engine has since become.
    return ListPlayerRatings(ratings=ratings)


ListPlayerRatingsDep = Annotated[ListPlayerRatings, Depends(get_list_player_ratings)]
