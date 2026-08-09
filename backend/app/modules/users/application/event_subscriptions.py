from __future__ import annotations

from app.application.events import EventDispatcher, EventCatalog
from app.modules.users.application.handlers import (
    LogUserDisabled,
    LogUserPromotedToAdmin,
    LogUserRegistered,
)
from app.modules.users.domain.events import (
    UserDisabled,
    UserPromotedToAdmin,
    UserRegistered,
)


def register_user_events(catalog: EventCatalog) -> None:
    catalog.register(UserRegistered, name="users.user_registered", version=1)
    catalog.register(UserDisabled, name="users.user_disabled", version=1)
    catalog.register(
        UserPromotedToAdmin, name="users.user_promoted_to_admin", version=1
    )


def subscribe_user_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(UserRegistered, LogUserRegistered())
    dispatcher.subscribe(UserDisabled, LogUserDisabled())
    dispatcher.subscribe(UserPromotedToAdmin, LogUserPromotedToAdmin())
