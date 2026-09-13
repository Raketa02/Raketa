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

**All four are at version 2, and version 1 is not registered.** Version 1
carried ``game_id``; ``docs/adr/0164`` §1 re-keyed the Plan on its challenge
and the payload now carries ``challenge_id``, which is a change to the wire
shape and is versioned as one rather than reinterpreted. There is no reader for
version 1, deliberately: no environment but ``local`` has ever run, its database
is disposable, and a row written under the old shape is a decoding error rather
than a stream folded wrongly — the day a build ships, this sentence stops being
available and the next such change keeps both versions readable.
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


#: The wire version every plan event is written under. See the module docstring
#: for why it is 2 and why 1 is not readable.
PLAN_EVENT_VERSION = 2


def register_plan_events(catalog: EventCatalog) -> None:
    for event_cls, name in _CONTRACTS:
        catalog.register(event_cls, name=name, version=PLAN_EVENT_VERSION)


def subscribe_plan_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogPlanEvent(name))
