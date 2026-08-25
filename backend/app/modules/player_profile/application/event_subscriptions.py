"""The Player profile context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to: renaming ``PlayerProfileCreated`` must never change what is already in the
store. ``player_profile.proposals_opt_in_answered`` is the one most likely to be
asked to carry more later — a jurisdiction, a policy id — and that will be
version 2 registered beside version 1, never an edit to it.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.player_profile.application.handlers import LogPlayerProfileEvent
from app.modules.player_profile.domain.events import (
    AvailabilityChanged,
    LocationChanged,
    PhotosChanged,
    PlayerProfileCreated,
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
    (ProposalsOptInAnswered, "player_profile.proposals_opt_in_answered"),
)


def register_player_profile_events(catalog: EventCatalog) -> None:
    for event_cls, name in _CONTRACTS:
        catalog.register(event_cls, name=name, version=1)


def subscribe_player_profile_handlers(dispatcher: EventDispatcher) -> None:
    for event_cls, name in _CONTRACTS:
        dispatcher.subscribe(event_cls, LogPlayerProfileEvent(name))
