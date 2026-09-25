from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from app.core.config import Settings
from app.modules.auth.domain.audience import UNSTATED_AUDIENCE, Audience
from app.modules.auth.domain.ports import IssuedToken

_ACCESS = "access"
_REFRESH = "refresh"


class JwtTokenService:
    """`TokenService` port implementation backed by PyJWT (HS256 by default).

    **The audience is the standard ``aud`` claim, checked here rather than by
    PyJWT.** PyJWT can only require one or refuse one, and neither is the rule:
    a token with no ``aud`` is a player-app token issued before audiences existed
    (``docs/adr/0185`` §6), so it must be admitted on the player surface and
    refused on the club surface. PyJWT's own check is therefore switched off and
    the claim compared below, after the signature, the issuer and the expiry
    have all passed.
    """

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._issuer = settings.JWT_ISSUER
        self._access_seconds = settings.ACCESS_TOKEN_EXPIRE_SECONDS
        self._refresh_seconds = settings.REFRESH_TOKEN_EXPIRE_SECONDS

    def issue_access(self, subject: str, *, audience: Audience) -> IssuedToken:
        return self._encode(subject, _ACCESS, self._access_seconds, audience)

    def issue_refresh(self, subject: str, *, audience: Audience) -> IssuedToken:
        return self._encode(subject, _REFRESH, self._refresh_seconds, audience)

    def decode_access(self, token: str, *, audience: Audience) -> Dict[str, Any]:
        return self._decode(token, _ACCESS, audience)

    def decode_refresh(self, token: str, *, audience: Audience) -> Dict[str, Any]:
        return self._decode(token, _REFRESH, audience)

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
        audience: Audience,
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
            "aud": audience.value,
            "jti": jti,
        }
        if extra:
            payload.update(extra)
        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        return IssuedToken(token=token, jti=jti, expires_at=exp)

    def _decode(
        self, token: str, expected_type: str, expected_audience: Audience
    ) -> Dict[str, Any]:
        payload = jwt.decode(
            token,
            self._secret,
            algorithms=[self._algorithm],
            issuer=self._issuer,
            options={"require": ["exp", "iat", "sub", "jti"], "verify_aud": False},
        )
        got = payload.get("token_type")
        if got != expected_type:
            raise jwt.InvalidTokenError(
                f"expected token_type={expected_type}, got {got!r}"
            )
        # Compared as a string, so a list-valued ``aud`` — legal JWT, never
        # minted here — is refused rather than searched.
        read_as = payload.get("aud", UNSTATED_AUDIENCE.value)
        if read_as != expected_audience.value:
            raise jwt.InvalidAudienceError(
                f"expected aud={expected_audience.value}, got {read_as!r}"
            )
        return payload
