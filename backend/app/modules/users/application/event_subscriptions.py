from __future__ import annotations

from app.application.events import EventDispatcher, EventCatalog
from app.modules.users.application.handlers import (
    LogUserDisabled,
    LogUserNamed,
    LogUserPromotedToAdmin,
    LogUserRegistered,
)
from app.modules.users.domain.events import (
    UserDisabled,
    UserNamed,
    UserPromotedToAdmin,
    UserRegistered,
)


def register_user_events(catalog: EventCatalog) -> None:
    catalog.register(UserRegistered, name="users.user_registered", version=1)
    catalog.register(UserNamed, name="users.user_named", version=1)
    catalog.register(UserDisabled, name="users.user_disabled", version=1)
    catalog.register(
        UserPromotedToAdmin, name="users.user_promoted_to_admin", version=1
    )


def subscribe_user_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(UserRegistered, LogUserRegistered())
    dispatcher.subscribe(UserNamed, LogUserNamed())
    dispatcher.subscribe(UserDisabled, LogUserDisabled())
    dispatcher.subscribe(UserPromotedToAdmin, LogUserPromotedToAdmin())
