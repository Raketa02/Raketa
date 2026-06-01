from __future__ import annotations

from dataclasses import dataclass

import jwt

from app.application.ports import DomainEventPublisher, UnitOfWork
from app.modules.auth.domain.ports import (
    PasswordHasher,
    RefreshTokenRepository,
    TokenService,
)
from app.shared.clock import Clock


@dataclass(frozen=True)
class LogoutCommand:
    presented_token: str


class Logout:
    """Idempotent: revoke the refresh token if recognised, otherwise no-op.

    We deliberately swallow validation failures and missing-token lookups —
    logout must not leak whether a given token exists.
    """

    def __init__(
        self,
        tokens: RefreshTokenRepository,
        jwt_service: TokenService,
        hasher: PasswordHasher,
        uow: UnitOfWork,
        clock: Clock,
        events: DomainEventPublisher,
    ) -> None:
        self._tokens = tokens
        self._jwt = jwt_service
        self._hasher = hasher
        self._uow = uow
        self._clock = clock
        self._events = events

    async def execute(self, command: LogoutCommand) -> None:
        try:
            payload = self._jwt.decode_refresh(command.presented_token)
        except jwt.InvalidTokenError:
            return
        stored = await self._tokens.get_by_jti(payload.get("jti", ""))
        if stored is None or not stored.is_valid:
            return
        if not self._hasher.verify(command.presented_token, stored.token_hash):
            return
        now = self._clock.now()
        stored.revoke(now=now, reason="logout")
        await self._tokens.revoke(stored, now=now)
        await self._events.publish_many(stored.pull_events())
        await self._uow.commit()
