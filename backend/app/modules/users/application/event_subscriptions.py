"""The Users context's durable event names, and who hears them.

**``users.user_named`` and ``users.account_opened_by_invitation`` are written
as version 2** (``docs/adr/0199`` §6): neither carries a player name any more.
Each **version 1 stays registered, decode-only** — ``UserNamedV1`` and
``AccountOpenedByInvitationV1`` — and the fold reads it with its name ignored,
so a stored row still replays and no account holds a name. Each is subscribed
to the same log line as its successor, because a v1 row still in the outbox is
delivered like any other.

**``users.user_marked_as_tester`` and ``users.user_unmarked_as_tester`` are
gone** with the Tester mark and the feature flags it fed (#581). They are not
kept decode-only, as ``games.dismissed`` is: PRD #569 resets the local store
with the removal and only ``local`` has ever run, so a stored row under either
name is a decoding error rather than a mark nothing reads.
"""

from __future__ import annotations

from app.application.events import EventDispatcher, EventCatalog
from app.modules.users.application.handlers import (
    LogAccountOpenedByInvitation,
    LogAdultAttested,
    LogPasswordChanged,
    LogPasswordCleared,
    LogUserDisabled,
    LogUserNamed,
    LogUserPromotedToAdmin,
    LogUserRegistered,
)
from app.modules.users.domain.events import (
    AccountOpenedByInvitation,
    AccountOpenedByInvitationV1,
    AdultAttested,
    PasswordChanged,
    PasswordCleared,
    UserDisabled,
    UserNamed,
    UserNamedV1,
    UserPromotedToAdmin,
    UserRegistered,
)

#: The wire version the naming is written under (``docs/adr/0199`` §6).
USER_NAMED_VERSION = 2
#: The wire version an Invitation's opening is written under (§4, §6).
ACCOUNT_OPENED_BY_INVITATION_VERSION = 2


def register_user_events(catalog: EventCatalog) -> None:
    catalog.register(UserRegistered, name="users.user_registered", version=1)
    catalog.register(UserNamedV1, name="users.user_named", version=1)
    catalog.register(UserNamed, name="users.user_named", version=USER_NAMED_VERSION)
    catalog.register(UserDisabled, name="users.user_disabled", version=1)
    catalog.register(PasswordChanged, name="users.password_changed", version=1)
    catalog.register(
        UserPromotedToAdmin, name="users.user_promoted_to_admin", version=1
    )
    catalog.register(
        AccountOpenedByInvitationV1,
        name="users.account_opened_by_invitation",
        version=1,
    )
    catalog.register(
        AccountOpenedByInvitation,
        name="users.account_opened_by_invitation",
        version=ACCOUNT_OPENED_BY_INVITATION_VERSION,
    )
    catalog.register(AdultAttested, name="users.adult_attested", version=1)
    catalog.register(PasswordCleared, name="users.password_cleared", version=1)


def subscribe_user_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(UserRegistered, LogUserRegistered())
    dispatcher.subscribe(UserNamed, LogUserNamed())
    dispatcher.subscribe(UserNamedV1, LogUserNamed())
    dispatcher.subscribe(UserDisabled, LogUserDisabled())
    dispatcher.subscribe(PasswordChanged, LogPasswordChanged())
    dispatcher.subscribe(UserPromotedToAdmin, LogUserPromotedToAdmin())
    dispatcher.subscribe(AccountOpenedByInvitation, LogAccountOpenedByInvitation())
    dispatcher.subscribe(AccountOpenedByInvitationV1, LogAccountOpenedByInvitation())
    dispatcher.subscribe(AdultAttested, LogAdultAttested())
    dispatcher.subscribe(PasswordCleared, LogPasswordCleared())
