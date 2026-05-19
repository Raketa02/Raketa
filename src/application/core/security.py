import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from application.core.config import Settings


class PasswordHasher:
    """Wraps bcrypt so callers never touch the primitive directly."""

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False


@dataclass
class IssuedToken:
    token: str
    jti: str
    expires_at: datetime


class JwtService:
    """Encodes / decodes typed JWTs. token_type ('access'|'refresh') is enforced
    on decode to prevent cross-type reuse (refresh-as-access etc.)."""

    ACCESS = "access"
    REFRESH = "refresh"

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._issuer = settings.JWT_ISSUER
        self._access_seconds = settings.ACCESS_TOKEN_EXPIRE_SECONDS
        self._refresh_seconds = settings.REFRESH_TOKEN_EXPIRE_SECONDS

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

    def issue_access(
        self, subject: str, extra: Optional[Dict[str, Any]] = None
    ) -> IssuedToken:
        return self._encode(subject, self.ACCESS, self._access_seconds, extra)

    def issue_refresh(
        self, subject: str, extra: Optional[Dict[str, Any]] = None
    ) -> IssuedToken:
        return self._encode(subject, self.REFRESH, self._refresh_seconds, extra)

    def decode(self, token: str, expected_type: str) -> Dict[str, Any]:
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

    @property
    def access_ttl_seconds(self) -> int:
        return self._access_seconds

    @property
    def refresh_ttl_seconds(self) -> int:
        return self._refresh_seconds
