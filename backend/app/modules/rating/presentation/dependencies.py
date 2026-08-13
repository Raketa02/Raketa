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
from app.modules.rating.application.create_assessment import CreateAssessment
from app.modules.rating.application.submit_answer import SubmitAnswer


def get_assessment_engine() -> AssessmentEngine:
    # The concrete engine version is chosen here, at the boundary; the use cases
    # depend only on the ``AssessmentEngine`` abstraction, so a version swap is a
    # one-line change.
    return RacketSkillEngineV3()


AssessmentEngineDep = Annotated[AssessmentEngine, Depends(get_assessment_engine)]


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
