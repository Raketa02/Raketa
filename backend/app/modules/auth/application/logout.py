from __future__ import annotations

from dataclasses import dataclass

import jwt

from app.application.ports import DomainEventPublisher, UnitOfWork
from app.kernel import Clock
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.ports import (
    PasswordHasher,
    RefreshTokenRepository,
    TokenService,
)


@dataclass(frozen=True)
class LogoutCommand:
    presented_token: str


class Logout:
    """Idempotent: revoke the refresh token if recognised, otherwise no-op.

    We deliberately swallow validation failures and missing-token lookups —
    logout must not leak whether a given token exists.

    **Built once per audience** (``docs/adr/0185`` §6), and a token the other
    surface issued is one of those swallowed failures: signing out of the club
    website never ends a session in the player app, even for the same email.
    """

    def __init__(
        self,
        *,
        audience: Audience,
        tokens: RefreshTokenRepository,
        jwt_service: TokenService,
        hasher: PasswordHasher,
        uow: UnitOfWork,
        clock: Clock,
        events: DomainEventPublisher,
    ) -> None:
        self._audience = audience
        self._tokens = tokens
        self._jwt = jwt_service
        self._hasher = hasher
        self._uow = uow
        self._clock = clock
        self._events = events

    async def execute(self, command: LogoutCommand) -> None:
        try:
            payload = self._jwt.decode_refresh(
                command.presented_token, audience=self._audience
            )
        except jwt.InvalidTokenError:
            return
        stored = await self._tokens.get_by_jti(payload.get("jti", ""))
        if stored is None or stored.audience is not self._audience:
            return
        if not stored.is_valid:
            return
        if not self._hasher.verify(command.presented_token, stored.token_hash):
            return
        now = self._clock.now()
        stored.revoke(now=now, reason="logout")
        await self._tokens.revoke(stored, now=now)
        await self._events.publish_many(stored.pull_events())
        await self._uow.commit()
