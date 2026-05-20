from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID


@dataclass
class RefreshToken:
    """Persisted state for a single issued refresh JWT.

    The plaintext token never lives on this entity — only its bcrypt hash and
    its `jti` so we can locate + verify it on refresh / logout.
    """

    id: UUID
    user_id: UUID
    token_hash: str
    jti: str
    refresh_expires_at: datetime
    is_valid: bool = True
    revoked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_expired(self, *, now: datetime) -> bool:
        exp = self.refresh_expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp <= now

    def revoke(self, *, now: datetime) -> None:
        self.is_valid = False
        self.revoked_at = now
