from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.administrators.application.handlers import LogAdministratorEvent
from app.modules.administrators.domain.events import (
    AdministratorInvited,
    AdministratorPasswordReset,
    AdministratorRemoved,
    InvitationAccepted,
    InvitationResent,
)

_EVENTS = (
    (AdministratorInvited, "administrators.administrator_invited"),
    (InvitationResent, "administrators.invitation_resent"),
    (InvitationAccepted, "administrators.invitation_accepted"),
    (AdministratorPasswordReset, "administrators.administrator_password_reset"),
    (AdministratorRemoved, "administrators.administrator_removed"),
)


def register_administrator_events(catalog: EventCatalog) -> None:
    for event_class, name in _EVENTS:
        catalog.register(event_class, name=name, version=1)


def subscribe_administrator_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(AdministratorInvited, LogAdministratorEvent())
    dispatcher.subscribe(InvitationResent, LogAdministratorEvent())
    dispatcher.subscribe(InvitationAccepted, LogAdministratorEvent())
    dispatcher.subscribe(AdministratorPasswordReset, LogAdministratorEvent())
    dispatcher.subscribe(AdministratorRemoved, LogAdministratorEvent())
