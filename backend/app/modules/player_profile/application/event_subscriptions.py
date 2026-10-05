"""The Player profile context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to: renaming ``PlayerProfileCreated`` must never change what is already in the
store. ``player_profile.proposals_opt_in_answered`` is the one most likely to be
asked to carry more later — a jurisdiction, a policy id — and that will be
version 2 registered beside version 1, never an edit to it.

**Twelve names, on two aggregates.** ``player_profile.play_intent_declared`` is
a ``PlayIntentDeclaration`` stream and not a profile one (``docs/adr/0094``); it
is registered here because a *context* owns its durable names, and the prefix is
therefore the context's rather than the aggregate's. Splitting the prefix would
have made the name a statement about which class writes it, which is the one
thing a durable name must not be.

**``player_profile.created`` is at version 2, and version 1 is not
registered.** Version 1 carried a week of mornings, afternoons and evenings;
``docs/adr/0189`` §5 made the week hours and the field ``weekly_hours``, which
is a change to the wire shape and is versioned as one — ``domain/events.py``
says why version 1 is deliberately unreadable. The week's own edit is
``player_profile.weekly_hours_set``, a new contract replacing
``player_profile.availability_changed``, which nothing reads any more.

**The v1 registrations beside it are none of them an edit.**
``gender_changed``, ``gender_preference_changed``, ``play_intent_declared``,
``intro_written``, ``intro_changed`` and ``weekly_hours_set`` are new contracts;
``player_profile.created`` gained two fields while it was still v1, which was
legitimate only because both were appended with defaults and every row then in
the store still decoded into the class (``domain/events.py`` says what each
absence means). A field that could **not**
be defaulted honestly would have been version 2 registered beside version 1
instead — which is why the intro is ``intro_written`` rather than a field on
``created`` (``docs/adr/0170`` §1) — and why its edit is ``intro_changed``
rather than ``intro_written`` told again: a withdrawal is a ``null`` the commit's
event cannot carry (``docs/adr/0179`` §6). These are the contracts the candidate
index reads (#182).
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.player_profile.application.handlers import LogPlayerProfileEvent
from app.modules.player_profile.domain.events import (
    GenderChanged,
    GenderPreferenceChanged,
    IntroChanged,
    IntroWritten,
    LocationChanged,
    PhotosChanged,
    PlayerProfileCreated,
    PlayIntentDeclared,
    ProposalsOptInAnswered,
    SearchRadiusChanged,
    SocialTagsChanged,
    WeeklyHoursSet,
)

#: The wire version ``player_profile.created`` is written under — see the module
#: docstring for why it is 2 and why 1 is not readable.
PROFILE_CREATED_VERSION = 2

#: Each durable name **with the version it is written under**, so a version is
#: read off the contract it belongs to rather than decided beside the loop.
_CONTRACTS = (
    (PlayerProfileCreated, "player_profile.created", PROFILE_CREATED_VERSION),
    (SocialTagsChanged, "player_profile.social_tags_changed", 1),
    (PhotosChanged, "player_profile.photos_changed", 1),
    (WeeklyHoursSet, "player_profile.weekly_hours_set", 1),
    (LocationChanged, "player_profile.location_changed", 1),
    (SearchRadiusChanged, "player_profile.search_radius_changed", 1),
    (GenderChanged, "player_profile.gender_changed", 1),
    (GenderPreferenceChanged, "player_profile.gender_preference_changed", 1),
    (IntroWritten, "player_profile.intro_written", 1),
    (IntroChanged, "player_profile.intro_changed", 1),
    (ProposalsOptInAnswered, "player_profile.proposals_opt_in_answered", 1),
    (PlayIntentDeclared, "player_profile.play_intent_declared", 1),
)


def register_player_profile_events(catalog: EventCatalog) -> None:
    for event_cls, name, version in _CONTRACTS:
        catalog.register(event_cls, name=name, version=version)


def subscribe_player_profile_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name, _ in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogPlayerProfileEvent(name))
