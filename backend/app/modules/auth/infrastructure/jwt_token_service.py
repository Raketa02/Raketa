from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from app.core.config import Settings
from app.modules.auth.domain.ports import IssuedToken

_ACCESS = "access"
_REFRESH = "refresh"


class JwtTokenService:
    """`TokenService` port implementation backed by PyJWT (HS256 by default)."""

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._issuer = settings.JWT_ISSUER
        self._access_seconds = settings.ACCESS_TOKEN_EXPIRE_SECONDS
        self._refresh_seconds = settings.REFRESH_TOKEN_EXPIRE_SECONDS

    def issue_access(self, subject: str) -> IssuedToken:
        return self._encode(subject, _ACCESS, self._access_seconds)

    def issue_refresh(self, subject: str) -> IssuedToken:
        return self._encode(subject, _REFRESH, self._refresh_seconds)

    def decode_access(self, token: str) -> Dict[str, Any]:
        return self._decode(token, _ACCESS)

    def decode_refresh(self, token: str) -> Dict[str, Any]:
        return self._decode(token, _REFRESH)

    @property
    def access_ttl_seconds(self) -> int:
        return self._access_seconds

    @property
    def refresh_ttl_seconds(self) -> int:
        return self._refresh_seconds

    def _encode(
        self,
        subject: str,
        token_type: str,
        ttl_seconds: int,
        extra: Optional[Dict[str, Any]] = None,
    ) -> IssuedToken:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(seconds=ttl_seconds)
        jti = uuid.uuid4().hex
        payload: Dict[str, Any] = {
            "sub": str(subject),
            "token_type": token_type,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "iss": self._issuer,
            "jti": jti,
        }
        if extra:
            payload.update(extra)
        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        return IssuedToken(token=token, jti=jti, expires_at=exp)

    def _decode(self, token: str, expected_type: str) -> Dict[str, Any]:
        payload = jwt.decode(
            token,
            self._secret,
            algorithms=[self._algorithm],
            issuer=self._issuer,
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
        got = payload.get("token_type")
        if got != expected_type:
            raise jwt.InvalidTokenError(
                f"expected token_type={expected_type}, got {got!r}"
            )
        return payload
