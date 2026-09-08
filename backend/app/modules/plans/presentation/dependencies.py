"""Request-scoped declarations for the plans context.

*When* each adapter is built and how long it lives, never *what* — every concrete
class comes from ``app.bootstrap.composition``, and
``tests/unit/test_composition_root.py`` fails this file if it imports one.

**The repository is built beside the unit of work it will commit through**, for
the reason every aggregate repository in this codebase is: it remembers the
stream versions it loaded, so it must never outlive the transaction it was built
for.

**The court is built per request and not per unit of work.** It reads ``games``
and writes nothing, so unlike the repository beside it there is no transaction it
could outlive — and the three writes and the one read all want the same one.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_plan_hold_query,
    build_plan_repository,
    build_planning_court,
    build_read_plans,
)
from app.modules.games.domain.ports import PlanningCourt
from app.modules.plans.application.read_plans import ReadPlans
from app.modules.plans.application.record_a_slot import SetDay, SetHour, SetPlace
from app.modules.plans.domain.ports import AccountHoldQuery, PlanRepository


def get_plan_repository(
    event_store: DomainEventStoreDep, events: EventPublisherDep
) -> PlanRepository:
    return build_plan_repository(event_store=event_store, events=events)


PlanRepositoryDep = Annotated[PlanRepository, Depends(get_plan_repository)]


def get_planning_court(db: DbSession) -> PlanningCourt:
    return build_planning_court(db)


PlanningCourtDep = Annotated[PlanningCourt, Depends(get_planning_court)]


def get_plan_hold_query(db: DbSession) -> AccountHoldQuery:
    return build_plan_hold_query(db)


PlanHoldQueryDep = Annotated[AccountHoldQuery, Depends(get_plan_hold_query)]


def get_read_plans(db: DbSession, clock: ClockDep) -> ReadPlans:
    """**Through the composition root's own assembly, not a second one.**

    The seed reads plans too, and *a seed run gets the wiring a request gets
    instead of a copy of it* — so this declares when the read is built and how
    long it lives, and `build_read_plans` decides what it is made of. Passing the
    request's own court in here would be the copy, one collaborator wide.
    """

    return build_read_plans(db, clock=clock)


ReadPlansDep = Annotated[ReadPlans, Depends(get_read_plans)]


def get_set_place(
    plans: PlanRepositoryDep,
    court: PlanningCourtDep,
    holds: PlanHoldQueryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SetPlace:
    return SetPlace(plans=plans, court=court, holds=holds, uow=uow, clock=clock)


SetPlaceDep = Annotated[SetPlace, Depends(get_set_place)]


def get_set_day(
    plans: PlanRepositoryDep,
    court: PlanningCourtDep,
    holds: PlanHoldQueryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SetDay:
    return SetDay(plans=plans, court=court, holds=holds, uow=uow, clock=clock)


SetDayDep = Annotated[SetDay, Depends(get_set_day)]


def get_set_hour(
    plans: PlanRepositoryDep,
    court: PlanningCourtDep,
    holds: PlanHoldQueryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SetHour:
    return SetHour(plans=plans, court=court, holds=holds, uow=uow, clock=clock)


SetHourDep = Annotated[SetHour, Depends(get_set_hour)]
