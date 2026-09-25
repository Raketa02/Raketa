from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.groups.application.handlers import (
    LogGroupJoined,
    LogJoinRequestApproved,
    LogJoinRequestDeclined,
    LogJoinRequested,
    LogPlayerGroupCreated,
)
from app.modules.groups.domain.events import (
    GroupJoined,
    JoinRequestApproved,
    JoinRequestDeclined,
    JoinRequested,
    PlayerGroupCreated,
)


def register_group_events(catalog: EventCatalog) -> None:
    catalog.register(PlayerGroupCreated, name="groups.player_group_created", version=1)
    catalog.register(GroupJoined, name="groups.group_joined", version=1)
    catalog.register(JoinRequested, name="groups.join_requested", version=1)
    catalog.register(
        JoinRequestApproved, name="groups.join_request_approved", version=1
    )
    catalog.register(
        JoinRequestDeclined, name="groups.join_request_declined", version=1
    )


def subscribe_group_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(PlayerGroupCreated, LogPlayerGroupCreated())
    dispatcher.subscribe(GroupJoined, LogGroupJoined())
    dispatcher.subscribe(JoinRequested, LogJoinRequested())
    dispatcher.subscribe(JoinRequestApproved, LogJoinRequestApproved())
    dispatcher.subscribe(JoinRequestDeclined, LogJoinRequestDeclined())
