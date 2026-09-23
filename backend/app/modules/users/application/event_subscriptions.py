from __future__ import annotations

from app.application.events import EventDispatcher, EventCatalog
from app.modules.users.application.handlers import (
    LogUserDisabled,
    LogUserMarkedAsTester,
    LogUserNamed,
    LogUserPromotedToAdmin,
    LogUserRegistered,
    LogUserUnmarkedAsTester,
)
from app.modules.users.domain.events import (
    UserDisabled,
    UserMarkedAsTester,
    UserNamed,
    UserPromotedToAdmin,
    UserRegistered,
    UserUnmarkedAsTester,
)


def register_user_events(catalog: EventCatalog) -> None:
    catalog.register(UserRegistered, name="users.user_registered", version=1)
    catalog.register(UserNamed, name="users.user_named", version=1)
    catalog.register(UserDisabled, name="users.user_disabled", version=1)
    catalog.register(
        UserPromotedToAdmin, name="users.user_promoted_to_admin", version=1
    )
    catalog.register(UserMarkedAsTester, name="users.user_marked_as_tester", version=1)
    catalog.register(
        UserUnmarkedAsTester, name="users.user_unmarked_as_tester", version=1
    )


def subscribe_user_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(UserRegistered, LogUserRegistered())
    dispatcher.subscribe(UserNamed, LogUserNamed())
    dispatcher.subscribe(UserDisabled, LogUserDisabled())
    dispatcher.subscribe(UserPromotedToAdmin, LogUserPromotedToAdmin())
    dispatcher.subscribe(UserMarkedAsTester, LogUserMarkedAsTester())
    dispatcher.subscribe(UserUnmarkedAsTester, LogUserUnmarkedAsTester())
