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


def register_auth_events(catalog: EventCatalog) -> None:
    catalog.register(RefreshTokenIssued, name="auth.refresh_token_issued", version=1)
    catalog.register(RefreshTokenRevoked, name="auth.refresh_token_revoked", version=1)
    catalog.register(RefreshTokenRotated, name="auth.refresh_token_rotated", version=1)


def subscribe_auth_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(RefreshTokenIssued, LogRefreshTokenIssued())
    dispatcher.subscribe(RefreshTokenRevoked, LogRefreshTokenRevoked())
    dispatcher.subscribe(RefreshTokenRotated, LogRefreshTokenRotated())
