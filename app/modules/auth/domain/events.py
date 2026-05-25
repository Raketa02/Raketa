from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class RefreshTokenIssued:
    token_id: UUID
    user_id: UUID
    jti: str
    expires_at: datetime
    occurred_at: datetime


@dataclass(frozen=True)
class RefreshTokenRevoked:
    token_id: UUID
    user_id: UUID
    jti: str
    reason: str
    occurred_at: datetime


@dataclass(frozen=True)
class RefreshTokenRotated:
    user_id: UUID
    revoked_token_id: UUID
    revoked_jti: str
    issued_token_id: UUID
    issued_jti: str
    occurred_at: datetime
