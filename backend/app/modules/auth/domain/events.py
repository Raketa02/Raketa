"""What happens to a refresh token, told through the outbox.

**Each names the account and the audience** (``docs/adr/0185`` §6). The account
is a User on the player app and a Club account on the club website, so the field
is ``account_id`` rather than a word that is true of only one of them, and the
audience — an ``Audience`` value, as ``UserRegistered.authority`` is an
``Authority`` value — says which kind it is. **That is a new stored shape**, so
all three are written at version 2 and version 1 is not readable
(``auth/application/event_subscriptions.py`` says why).
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class RefreshTokenIssued:
    token_id: UUID
    account_id: UUID
    jti: str
    expires_at: datetime
    occurred_at: datetime
    audience: str


@dataclass(frozen=True)
class RefreshTokenRevoked:
    token_id: UUID
    account_id: UUID
    jti: str
    reason: str
    occurred_at: datetime
    audience: str


@dataclass(frozen=True)
class RefreshTokenRotated:
    account_id: UUID
    revoked_token_id: UUID
    revoked_jti: str
    issued_token_id: UUID
    issued_jti: str
    occurred_at: datetime
    audience: str
