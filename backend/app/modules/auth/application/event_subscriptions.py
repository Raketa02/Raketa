"""The refresh token's three events, and why they are at version 2.

**Version 1 is not registered.** It carried ``user_id``; since
``docs/adr/0185`` §6 a token may be a Club account's as well as a User's, and
the payload carries ``account_id`` and the ``audience`` instead — a change to
the stored shape, versioned as one rather than reinterpreted. There is no reader
for version 1, deliberately, on the argument ``plans`` made for its own re-key:
no environment but ``local`` has ever run, these events are only ever in the
outbox and are delivered to loggers within seconds, and a row written under the
old shape is a decoding error rather than a token filed under the wrong kind of
account. The day a build ships, that argument stops being available and the
next such change keeps both versions readable.
"""

from __future__ import annotations

from app.application.events import EventDispatcher, EventCatalog
from app.modules.auth.application.handlers import (
    LogRefreshTokenIssued,
    LogRefreshTokenRevoked,
    LogRefreshTokenRotated,
)
from app.modules.auth.domain.events import (
    RefreshTokenIssued,
    RefreshTokenRevoked,
    RefreshTokenRotated,
)


#: The wire version every refresh-token event is written under. See the module
#: docstring for why it is 2 and why 1 is not readable.
REFRESH_TOKEN_EVENT_VERSION = 2


def register_auth_events(catalog: EventCatalog) -> None:
    catalog.register(
        RefreshTokenIssued,
        name="auth.refresh_token_issued",
        version=REFRESH_TOKEN_EVENT_VERSION,
    )
    catalog.register(
        RefreshTokenRevoked,
        name="auth.refresh_token_revoked",
        version=REFRESH_TOKEN_EVENT_VERSION,
    )
    catalog.register(
        RefreshTokenRotated,
        name="auth.refresh_token_rotated",
        version=REFRESH_TOKEN_EVENT_VERSION,
    )


def subscribe_auth_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(RefreshTokenIssued, LogRefreshTokenIssued())
    dispatcher.subscribe(RefreshTokenRevoked, LogRefreshTokenRevoked())
    dispatcher.subscribe(RefreshTokenRotated, LogRefreshTokenRotated())
