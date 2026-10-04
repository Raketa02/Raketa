"""Signing out everywhere: every refresh token an account holds, revoked.

The other half of ``docs/adr/0185`` §7. The account's **credentials-changed
instant** — which refuses every access token issued before it — is written by
the context that owns the account, on the row every request already reads; this
revokes the refresh tokens, so none of those sessions can be renewed either.

**One surface at a time**, because a token belongs to one: a club's password
reset signs the club website out and leaves a player who shares its email
signed in, as the two are different identities (``docs/adr/0182`` §3).

Nothing here commits; the act that changed the credentials does.
"""

from __future__ import annotations

from typing import Final
from uuid import UUID

from app.application.ports import DomainEventPublisher
from app.kernel import Instant
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.ports import RefreshTokenRepository

#: The ``reason`` each revoked token's event carries.
CREDENTIALS_CHANGED: Final = "credentials_changed"


class SignOutEverywhere:
    def __init__(
        self, *, tokens: RefreshTokenRepository, events: DomainEventPublisher
    ) -> None:
        self._tokens = tokens
        self._events = events

    async def execute(
        self, account_id: UUID, *, audience: Audience, now: Instant
    ) -> None:
        for token in await self._tokens.valid_tokens_of(account_id, audience=audience):
            token.revoke(now=now, reason=CREDENTIALS_CHANGED)
            await self._tokens.revoke(token, now=now)
            await self._events.publish_many(token.pull_events())
