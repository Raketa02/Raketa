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

**The six newest are v1 registrations and none of them is an edit.**
``gender_changed``, ``gender_preference_changed``, ``play_intent_declared``,
``intro_written`` and ``intro_changed`` are new contracts; ``player_profile.created``
gained two fields and stayed v1, which is legitimate only because both are
appended with defaults
and every row already in the store still decodes into the class
(``domain/events.py`` says what each absence means). A field that could **not**
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
    AvailabilityChanged,
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
)

_CONTRACTS = (
    (PlayerProfileCreated, "player_profile.created"),
    (SocialTagsChanged, "player_profile.social_tags_changed"),
    (PhotosChanged, "player_profile.photos_changed"),
    (AvailabilityChanged, "player_profile.availability_changed"),
    (LocationChanged, "player_profile.location_changed"),
    (SearchRadiusChanged, "player_profile.search_radius_changed"),
    (GenderChanged, "player_profile.gender_changed"),
    (GenderPreferenceChanged, "player_profile.gender_preference_changed"),
    (IntroWritten, "player_profile.intro_written"),
    (IntroChanged, "player_profile.intro_changed"),
    (ProposalsOptInAnswered, "player_profile.proposals_opt_in_answered"),
    (PlayIntentDeclared, "player_profile.play_intent_declared"),
)


def register_player_profile_events(catalog: EventCatalog) -> None:
    for event_cls, name in _CONTRACTS:
        catalog.register(event_cls, name=name, version=1)


def subscribe_player_profile_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogPlayerProfileEvent(name))
