from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from uuid import UUID

from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.refresh_token import RefreshToken


@dataclass(frozen=True)
class IssuedToken:
    token: str
    jti: str
    expires_at: datetime


@runtime_checkable
class TokenService(Protocol):
    """Mints + decodes typed JWTs. `token_type` is enforced on decode so an
    access token can never be presented where a refresh is expected, and vice
    versa.

    **The audience is enforced the same way** (``docs/adr/0185`` §6): every token
    is minted for one, and a decode names the one it expects and refuses any
    other with ``jwt.InvalidTokenError`` — so a club token presented to the
    player surface fails exactly as a forged one does. A token that names no
    audience is read as a player-app token (``UNSTATED_AUDIENCE``). Required on
    every call rather than defaulted, because a default is the audience nobody
    chose.
    """

    def issue_access(self, subject: str, *, audience: Audience) -> IssuedToken: ...
    def issue_refresh(self, subject: str, *, audience: Audience) -> IssuedToken: ...
    def decode_access(self, token: str, *, audience: Audience) -> Dict[str, Any]: ...
    def decode_refresh(self, token: str, *, audience: Audience) -> Dict[str, Any]: ...

    @property
    def access_ttl_seconds(self) -> int: ...

    @property
    def refresh_ttl_seconds(self) -> int: ...


@runtime_checkable
class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, password_hash: str) -> bool: ...


@runtime_checkable
class SessionHolders(Protocol):
    """The accounts behind one audience's sessions, asked on every refresh.

    A refresh rotates a pair for an account that may have been disabled since it
    signed in, so the rotation asks first. **Which accounts those are is the
    audience's** (``docs/adr/0185`` §6) — Users for the player app, Club accounts
    for the club website — and each context answers for its own and refuses in
    its own words: a player's refusal is ``user_not_eligible``, which the player
    app already branches on, and a club's is its own.
    """

    async def refuse_unless_eligible(self, account_id: UUID) -> None: ...


@runtime_checkable
class RefreshTokenRepository(Protocol):
    async def add(self, token: RefreshToken) -> RefreshToken: ...
    async def get_by_jti(self, jti: str) -> Optional[RefreshToken]: ...
    async def revoke(self, token: RefreshToken, *, now: datetime) -> None: ...
