from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.events import (
    RefreshTokenIssued,
    RefreshTokenRevoked,
    RefreshTokenRotated,
)
from app.shared.domain import DomainEvent, EventRecorder


@dataclass
class RefreshToken:
    """Persisted state for a single issued refresh JWT.

    The plaintext token never lives on this entity — only its bcrypt hash and
    its `jti` so we can locate + verify it on refresh / logout.

    Events raised by `issue`, `revoke`, and `rotate_to` are collected in the
    composed `EventRecorder` and drained by the application layer.

    **It records whose it is** (``docs/adr/0185`` §6): the account it was issued
    to, and the audience it was issued for — which says what kind of account
    that is, a User on the player app or a Club account on the club website. A
    refresh on one surface never rotates a token the other surface issued.
    """

    id: UUID
    account_id: UUID
    audience: Audience
    token_hash: str
    jti: str
    refresh_expires_at: datetime
    is_valid: bool = True
    revoked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def issue(
        cls,
        *,
        token_id: UUID,
        account_id: UUID,
        audience: Audience,
        token_hash: str,
        jti: str,
        refresh_expires_at: datetime,
        occurred_at: datetime,
    ) -> "RefreshToken":
        token = cls(
            id=token_id,
            account_id=account_id,
            audience=audience,
            token_hash=token_hash,
            jti=jti,
            refresh_expires_at=refresh_expires_at,
        )
        token._events.record(
            RefreshTokenIssued(
                token_id=token.id,
                account_id=token.account_id,
                jti=token.jti,
                expires_at=token.refresh_expires_at,
                occurred_at=occurred_at,
                audience=token.audience.value,
            )
        )
        return token

    def is_expired(self, *, now: datetime) -> bool:
        exp = self.refresh_expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp <= now

    def revoke(self, *, now: datetime, reason: str = "manual") -> None:
        if not self.is_valid:
            return
        self.is_valid = False
        self.revoked_at = now
        self._events.record(
            RefreshTokenRevoked(
                token_id=self.id,
                account_id=self.account_id,
                jti=self.jti,
                reason=reason,
                occurred_at=now,
                audience=self.audience.value,
            )
        )

    def rotate_to(self, new_token: "RefreshToken", *, now: datetime) -> None:
        if not self.is_valid:
            return
        self.is_valid = False
        self.revoked_at = now
        self._events.record(
            RefreshTokenRotated(
                account_id=self.account_id,
                revoked_token_id=self.id,
                revoked_jti=self.jti,
                issued_token_id=new_token.id,
                issued_jti=new_token.jti,
                occurred_at=now,
                audience=self.audience.value,
            )
        )
