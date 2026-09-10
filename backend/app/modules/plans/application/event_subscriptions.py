"""The Plan context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to: renaming ``DayRecorded`` must never change what is already in the store.

**Four names, on one aggregate, and every one of them is something a person
did.** There is no ``plans.opened``, because a plan is born by being used; no
``plans.completed``, because the third recording *is* the completion and a name
announcing it would be a conclusion the record already implies; and no
``plans.cancelled``, because a plan is never unmade.

**``plans.plan_locked`` is not ``plans.completed`` under another name**, and the
distinction is the whole of ``docs/adr/0155``. A completion is a conclusion the
record already implies — three slots are filled and anybody can see it. A lock is
a fact **nobody wrote down**: no arrangement of the three slots reaches *these
people have agreed*, which is exactly what ``docs/adr/0142`` §3 requires of an
event before it may announce anything. And there is no ``plans.unlocked``, for
the same reason there is no clearing name: the lock is a thing that happened.

**Setting a slot and moving one share a name**, which is the whole of ADR-0144's
*one fact told twice*. A ``plans.day_changed`` beside ``plans.day_recorded``
would be two durable contracts for one thing, and the room would have to decide
which sentence to write for each.

**One subscription here, and it is the audit line.** The subscriber that matters
is a **room**, and it is registered by the Conversation context over its own
delivery batch — this context does not know it exists and has no line of code
about it.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.plans.application.handlers import LogPlanEvent
from app.modules.plans.domain.events import (
    DayRecorded,
    HourRecorded,
    PlaceRecorded,
    PlanLocked,
)

_CONTRACTS = (
    (PlaceRecorded, "plans.place_recorded"),
    (DayRecorded, "plans.day_recorded"),
    (HourRecorded, "plans.hour_recorded"),
    (PlanLocked, "plans.plan_locked"),
)


def register_plan_events(catalog: EventCatalog) -> None:
    for event_cls, name in _CONTRACTS:
        catalog.register(event_cls, name=name, version=1)


def subscribe_plan_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogPlanEvent(name))
