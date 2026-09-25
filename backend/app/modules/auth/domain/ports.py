from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.one_time_credential import (
    CredentialPurpose,
    OneTimeCredential,
)
from app.modules.auth.domain.refresh_token import RefreshToken


#: The claim every token carries its issue instant in: microseconds since the
#: epoch, **on the application's clock** — the instant signing out everywhere
#: compares with an account's credentials-changed instant (``docs/adr/0185`` §7).
#: A token issued before it existed has none, and is read at its ``iat``.
ISSUED_AT_CLAIM = "iat_us"


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

    async def valid_tokens_of(
        self, account_id: UUID, *, audience: Audience
    ) -> list[RefreshToken]:
        """Every refresh token this account still holds on this surface — what
        signing out everywhere revokes (``docs/adr/0185`` §7)."""
        ...


@final
@dataclass(frozen=True, slots=True)
class PasswordAccount:
    """An account a password can be recovered for, as much as recovering it
    needs: which one, and the address its email goes to."""

    id: UUID
    email: str


@runtime_checkable
class PasswordAccounts(Protocol):
    """The accounts behind one audience's passwords, as *Forgot password?* sees
    them (``docs/adr/0184`` §5).

    **Which accounts those are is the audience's**, exactly as it is for
    ``SessionHolders``: Users for the player app, Club accounts for the club
    website. Each context answers for its own, and records the change on its own
    stream — so the credentials-changed instant that signs every older access
    token out (``docs/adr/0185`` §7) is written by the context whose row every
    request already reads.
    """

    async def recoverable(self, email: str) -> Optional[PasswordAccount]:
        """The account that signs in with this address on this surface and may
        still sign in at all, or ``None`` — for an address nobody holds and for
        an account that is disabled alike."""
        ...

    async def set_password(
        self, account_id: UUID, *, password_hash: str, at: Instant
    ) -> None:
        """Record the new password, and ``at`` as the instant every access token
        issued before it stops being accepted. In the caller's transaction,
        without committing it. Refuses as a sign-in would when the account can
        no longer sign in."""
        ...


@runtime_checkable
class CredentialSecrets(Protocol):
    """Where a credential's randomness comes from: a link token, or a ticket."""

    def mint(self) -> str:
        """256 random bits, URL-safe."""
        ...


@runtime_checkable
class OneTimeCredentialStore(Protocol):
    """The table credentials live in. **Never** the event store
    (``docs/adr/0184`` §4).

    **Every read claims what it returns until the caller's transaction ends**,
    because every read here is made to change what it found: a wrong code
    counted, a credential spent, an older one retired. Two claims at once are
    therefore one after the other, and *five wrong codes* means five."""

    async def add(self, credential: OneTimeCredential) -> None: ...

    async def save(self, credential: OneTimeCredential) -> None:
        """Write back what changed on a credential this store handed out."""
        ...

    async def by_token_hash(self, token_hash: str) -> Optional[OneTimeCredential]: ...

    async def by_ticket_hash(
        self, ticket_hash: str
    ) -> Optional[OneTimeCredential]: ...

    async def issued_to(
        self,
        email: str,
        *,
        purpose: CredentialPurpose,
        audience: Audience,
        since: Instant,
    ) -> list[OneTimeCredential]:
        """Every credential of this kind issued to this address on this surface
        after ``since`` — exclusive, so *the last hour* ends an hour after the
        first one — newest first: what a claim checks a code against, and what
        the request throttle counts."""
        ...

    async def live_for(
        self,
        subject_id: UUID,
        *,
        purpose: CredentialPurpose,
        audience: Audience,
        now: Instant,
    ) -> list[OneTimeCredential]:
        """Every credential of this kind for this subject that has not expired
        and not been used — what a newer one retires."""
        ...
