"""When Now's ports are built, and how long they live. Never *what* is built.

Every construction happens in ``app/bootstrap/composition.py``; these callables
only declare the lifetime, exactly as every other module's do. A test walks these
files and reddens if one imports an adapter, because the failure mode is one line
of convenience inside a ``Depends`` callable and nothing about a green suite would
look different afterwards.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DomainEventStoreDep,
    EventPublisherDep,
)
from app.bootstrap.composition import build_rated_sports, build_skill_rating_repository
from app.modules.now.application.compose_now import ComposeNow
from app.modules.now.domain.ports import RatedSports


def get_rated_sports(
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
) -> RatedSports:
    # Declared here rather than borrowed from the rating module's own dependency
    # file: one module reaching into another's presentation layer is a coupling
    # neither of them asked for, and both are three lines over the same factory.
    return build_rated_sports(
        build_skill_rating_repository(event_store=event_store, events=events)
    )


RatedSportsDep = Annotated[RatedSports, Depends(get_rated_sports)]


def get_compose_now(rated_sports: RatedSportsDep, clock: ClockDep) -> ComposeNow:
    return ComposeNow(rated_sports=rated_sports, clock=clock)


ComposeNowDep = Annotated[ComposeNow, Depends(get_compose_now)]
