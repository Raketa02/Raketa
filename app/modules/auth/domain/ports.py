from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Protocol, runtime_checkable

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
    versa."""

    def issue_access(self, subject: str) -> IssuedToken: ...
    def issue_refresh(self, subject: str) -> IssuedToken: ...
    def decode_access(self, token: str) -> Dict[str, Any]: ...
    def decode_refresh(self, token: str) -> Dict[str, Any]: ...

    @property
    def access_ttl_seconds(self) -> int: ...

    @property
    def refresh_ttl_seconds(self) -> int: ...


@runtime_checkable
class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, password_hash: str) -> bool: ...


@runtime_checkable
class RefreshTokenRepository(Protocol):
    async def add(self, token: RefreshToken) -> RefreshToken: ...
    async def get_by_jti(self, jti: str) -> Optional[RefreshToken]: ...
    async def revoke(self, token: RefreshToken, *, now: datetime) -> None: ...
