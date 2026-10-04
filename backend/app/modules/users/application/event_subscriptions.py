from __future__ import annotations

from app.application.events import EventDispatcher, EventCatalog
from app.modules.users.application.handlers import (
    LogAccountOpenedByInvitation,
    LogAdultAttested,
    LogPasswordChanged,
    LogPasswordCleared,
    LogUserDisabled,
    LogUserMarkedAsTester,
    LogUserNamed,
    LogUserPromotedToAdmin,
    LogUserRegistered,
    LogUserUnmarkedAsTester,
)
from app.modules.users.domain.events import (
    AccountOpenedByInvitation,
    AdultAttested,
    PasswordChanged,
    PasswordCleared,
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
    catalog.register(PasswordChanged, name="users.password_changed", version=1)
    catalog.register(
        UserPromotedToAdmin, name="users.user_promoted_to_admin", version=1
    )
    catalog.register(UserMarkedAsTester, name="users.user_marked_as_tester", version=1)
    catalog.register(
        UserUnmarkedAsTester, name="users.user_unmarked_as_tester", version=1
    )
    catalog.register(
        AccountOpenedByInvitation,
        name="users.account_opened_by_invitation",
        version=1,
    )
    catalog.register(AdultAttested, name="users.adult_attested", version=1)
    catalog.register(PasswordCleared, name="users.password_cleared", version=1)


def subscribe_user_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(UserRegistered, LogUserRegistered())
    dispatcher.subscribe(UserNamed, LogUserNamed())
    dispatcher.subscribe(UserDisabled, LogUserDisabled())
    dispatcher.subscribe(PasswordChanged, LogPasswordChanged())
    dispatcher.subscribe(UserPromotedToAdmin, LogUserPromotedToAdmin())
    dispatcher.subscribe(UserMarkedAsTester, LogUserMarkedAsTester())
    dispatcher.subscribe(UserUnmarkedAsTester, LogUserUnmarkedAsTester())
    dispatcher.subscribe(AccountOpenedByInvitation, LogAccountOpenedByInvitation())
    dispatcher.subscribe(AdultAttested, LogAdultAttested())
    dispatcher.subscribe(PasswordCleared, LogPasswordCleared())
