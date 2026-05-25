from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.infrastructure.database.unit_of_work import UnitOfWork
from app.modules.auth.domain.ports import (
    PasswordHasher,
    RefreshTokenRepository,
    TokenService,
)
from app.modules.auth.domain.refresh_token import RefreshToken
from app.shared.clock import Clock
from app.shared.events import DomainEventPublisher
from app.shared.ids import new_uuid


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class TokenRotator:
    """Application service that issues new JWT pairs and persists hashed
    refresh-token state. Reused by `Login` (fresh issuance) and
    `RefreshAuthTokens` (revoke-old + issue-new)."""

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

    async def issue_pair(self, user_id: UUID) -> TokenPair:
        access = self._jwt.issue_access(str(user_id))
        refresh = self._jwt.issue_refresh(str(user_id))
        refresh_record = self._new_refresh_token(user_id, refresh)

        await self._tokens.add(refresh_record)
        await self._events.publish_many(refresh_record.pull_events())
        await self._uow.commit()

        return TokenPair(
            access_token=access.token,
            refresh_token=refresh.token,
            expires_in=self._jwt.access_ttl_seconds,
        )

    async def rotate(self, stored: RefreshToken, user_id: UUID) -> TokenPair:
        access = self._jwt.issue_access(str(user_id))
        refresh = self._jwt.issue_refresh(str(user_id))
        refresh_record = self._new_refresh_token(user_id, refresh)
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

    def _new_refresh_token(self, user_id: UUID, refresh) -> RefreshToken:
        return RefreshToken.issue(
            token_id=new_uuid(),
            user_id=user_id,
            token_hash=self._hasher.hash(refresh.token),
            jti=refresh.jti,
            refresh_expires_at=refresh.expires_at,
            occurred_at=self._clock.now(),
        )
