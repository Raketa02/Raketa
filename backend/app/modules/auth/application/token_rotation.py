from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.ports import DomainEventPublisher, UnitOfWork
from app.kernel import Clock
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.ports import (
    PasswordHasher,
    RefreshTokenRepository,
    TokenService,
)
from app.modules.auth.domain.refresh_token import RefreshToken
from app.shared.ids import new_uuid


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class TokenRotator:
    """Application service that issues new JWT pairs and persists hashed
    refresh-token state. Reused by `Login` and the club's sign-in (fresh
    issuance) and `RefreshAuthTokens` (revoke-old + issue-new).

    **A pair is issued for one audience and rotated within it** (``docs/adr/0185``
    §6): a fresh pair names the audience it is for, and a rotation reads it off
    the token being rotated, so a refresh can never move a session from one
    surface to the other.
    """

    def __init__(
        self,
        tokens: RefreshTokenRepository,
        jwt: TokenService,
        hasher: PasswordHasher,
        uow: UnitOfWork,
        clock: Clock,
        events: DomainEventPublisher,
    ) -> None:
        self._tokens = tokens
        self._jwt = jwt
        self._hasher = hasher
        self._uow = uow
        self._clock = clock
        self._events = events

    async def issue_pair(self, account_id: UUID, *, audience: Audience) -> TokenPair:
        access = self._jwt.issue_access(str(account_id), audience=audience)
        refresh = self._jwt.issue_refresh(str(account_id), audience=audience)
        refresh_record = self._new_refresh_token(account_id, audience, refresh)

        await self._tokens.add(refresh_record)
        await self._events.publish_many(refresh_record.pull_events())
        await self._uow.commit()

        return TokenPair(
            access_token=access.token,
            refresh_token=refresh.token,
            expires_in=self._jwt.access_ttl_seconds,
        )

    async def rotate(self, stored: RefreshToken) -> TokenPair:
        account_id, audience = stored.account_id, stored.audience
        access = self._jwt.issue_access(str(account_id), audience=audience)
        refresh = self._jwt.issue_refresh(str(account_id), audience=audience)
        refresh_record = self._new_refresh_token(account_id, audience, refresh)
        now = self._clock.now()

        stored.rotate_to(refresh_record, now=now)
        await self._tokens.revoke(stored, now=now)
        await self._tokens.add(refresh_record)
        await self._events.publish_many(
            [*stored.pull_events(), *refresh_record.pull_events()]
        )
        await self._uow.commit()

        return TokenPair(
            access_token=access.token,
            refresh_token=refresh.token,
            expires_in=self._jwt.access_ttl_seconds,
        )

    def _new_refresh_token(
        self, account_id: UUID, audience: Audience, refresh
    ) -> RefreshToken:
        return RefreshToken.issue(
            token_id=new_uuid(),
            account_id=account_id,
            audience=audience,
            token_hash=self._hasher.hash(refresh.token),
            jti=refresh.jti,
            refresh_expires_at=refresh.expires_at,
            occurred_at=self._clock.now(),
        )
