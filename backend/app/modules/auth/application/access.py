"""An access token, read the one way every surface reads one.

Two surfaces authenticate their callers now — the player app's Users and the
club website's Club accounts (``docs/adr/0185`` §6) — and each must refuse a
token in exactly the same five ways, told apart by code: none sent, expired,
invalid (a forgery, the wrong type, or **another surface's audience**), a
subject that is not an id, and an expiry that cannot be read. Written once here
so that the two surfaces cannot drift into two ladders with one of them fixed
alone; what each does with the account id afterwards is its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import final
from uuid import UUID

import jwt

from app.kernel import Instant, instant
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.errors import (
    AccessTokenExpired,
    AccessTokenInvalid,
    AccessTokenMissing,
    AccessTokenSubjectMalformed,
)
from app.modules.auth.domain.ports import TokenService


@final
@dataclass(frozen=True, slots=True)
class AccessClaims:
    """Whose token it is, and when it stops being accepted."""

    account_id: UUID
    expires_at: Instant


def read_access_token(
    token_service: TokenService, raw_token: str | None, *, audience: Audience
) -> AccessClaims:
    """The claims of a bearer token presented to ``audience``'s surface.

    A token minted for the other surface is refused as ``access_token_invalid``
    — to this surface it is not a valid token, and naming the audience it *was*
    for would tell a caller something about the credential it is holding that
    no client needs.
    """

    if not raw_token:
        raise AccessTokenMissing()

    try:
        payload = token_service.decode_access(raw_token, audience=audience)
    except jwt.ExpiredSignatureError as exc:
        raise AccessTokenExpired() from exc
    except jwt.InvalidTokenError as exc:
        raise AccessTokenInvalid() from exc

    try:
        account_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise AccessTokenSubjectMalformed() from exc

    try:
        expires_at = instant(
            datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
        )
    except (KeyError, TypeError, ValueError, OverflowError, OSError) as exc:
        # **The fifth refusal, and it is not defensive.** An access token
        # with no readable expiry is one nothing can close a live stream on
        # (``docs/adr/0147`` §6), and a credential that never runs out is
        # exactly what ``docs/adr/0004`` refuses. ``JwtTokenService`` already
        # requires ``exp`` on decode, so this is the port's contract stated
        # where the port is consumed rather than trusted to every adapter.
        raise AccessTokenInvalid() from exc

    return AccessClaims(account_id=account_id, expires_at=expires_at)
