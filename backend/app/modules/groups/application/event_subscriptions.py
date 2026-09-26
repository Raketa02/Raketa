from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.groups.application.handlers import (
    LogAdministratorAssigned,
    LogGroupDeleted,
    LogGroupJoined,
    LogGroupLeft,
    LogGroupRenamed,
    LogJoinPolicyChanged,
    LogJoinRequestApproved,
    LogJoinRequestDeclined,
    LogJoinRequested,
    LogOfficialGroupCreated,
    LogOwnershipPassed,
    LogPlayerGroupCreated,
    LogSportsDeclared,
    LogWhatsAppSizeSet,
)
from app.modules.groups.domain.events import (
    AdministratorAssigned,
    GroupDeleted,
    GroupJoined,
    GroupLeft,
    GroupRenamed,
    JoinPolicyChanged,
    JoinRequestApproved,
    JoinRequestDeclined,
    JoinRequested,
    OfficialGroupCreated,
    OwnershipPassed,
    PlayerGroupCreated,
    SportsDeclared,
    WhatsAppSizeSet,
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
    catalog.register(OwnershipPassed, name="groups.ownership_passed", version=1)
    catalog.register(GroupLeft, name="groups.group_left", version=1)
    catalog.register(GroupRenamed, name="groups.group_renamed", version=1)
    catalog.register(JoinPolicyChanged, name="groups.join_policy_changed", version=1)
    catalog.register(GroupDeleted, name="groups.group_deleted", version=1)
    catalog.register(
        OfficialGroupCreated, name="groups.official_group_created", version=1
    )
    catalog.register(WhatsAppSizeSet, name="groups.whatsapp_size_set", version=1)
    catalog.register(SportsDeclared, name="groups.sports_declared", version=1)
    catalog.register(
        AdministratorAssigned, name="groups.administrator_assigned", version=1
    )


def subscribe_group_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(PlayerGroupCreated, LogPlayerGroupCreated())
    dispatcher.subscribe(GroupJoined, LogGroupJoined())
    dispatcher.subscribe(JoinRequested, LogJoinRequested())
    dispatcher.subscribe(JoinRequestApproved, LogJoinRequestApproved())
    dispatcher.subscribe(JoinRequestDeclined, LogJoinRequestDeclined())
    dispatcher.subscribe(OwnershipPassed, LogOwnershipPassed())
    dispatcher.subscribe(GroupLeft, LogGroupLeft())
    dispatcher.subscribe(GroupRenamed, LogGroupRenamed())
    dispatcher.subscribe(JoinPolicyChanged, LogJoinPolicyChanged())
    dispatcher.subscribe(GroupDeleted, LogGroupDeleted())
    dispatcher.subscribe(OfficialGroupCreated, LogOfficialGroupCreated())
    dispatcher.subscribe(WhatsAppSizeSet, LogWhatsAppSizeSet())
    dispatcher.subscribe(SportsDeclared, LogSportsDeclared())
    dispatcher.subscribe(AdministratorAssigned, LogAdministratorAssigned())
