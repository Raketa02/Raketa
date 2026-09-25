from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.groups.application.handlers import (
    LogGroupJoined,
    LogPlayerGroupCreated,
)
from app.modules.groups.domain.events import GroupJoined, PlayerGroupCreated


def register_group_events(catalog: EventCatalog) -> None:
    catalog.register(PlayerGroupCreated, name="groups.player_group_created", version=1)
    catalog.register(GroupJoined, name="groups.group_joined", version=1)


def subscribe_group_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(PlayerGroupCreated, LogPlayerGroupCreated())
    dispatcher.subscribe(GroupJoined, LogGroupJoined())
