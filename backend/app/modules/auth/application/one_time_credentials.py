"""The one-time credential mechanism, as every flow that issues one uses it.

*Forgot password?* is the first caller; an administrator's invitation and the
club's reset of one are the next (``docs/adr/0184`` §3). Each issues a
credential for **a purpose and an audience**, and each redeems one the same way,
so the rules — hashed, used once, expiring, locked by five wrong codes — are
written here once and tested once.

Nothing here commits. The caller's unit of work carries the credential, the
email that announces it and whatever the act changed, together.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Final, Optional, final
from uuid import UUID

from app.kernel import Instant, instant
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.credential_code import TypedCode, code_for
from app.modules.auth.domain.errors import (
    CredentialCodeIncorrect,
    CredentialNotFound,
)
from app.modules.auth.domain.one_time_credential import (
    CredentialPurpose,
    OneTimeCredential,
    Standing,
    digest_of,
)
from app.modules.auth.domain.ports import (
    CredentialSecrets,
    OneTimeCredentialStore,
    PasswordHasher,
)
from app.shared.ids import new_uuid

#: How far back a claim looks for the credential a code was sent with. Past the
#: longest lifetime by a margin, so a code typed a day after it expired is told
#: *expired* rather than *wrong* — and bounded, because each credential it finds
#: costs one hash comparison.
CLAIM_LOOKBACK: Final = timedelta(days=7)


@final
@dataclass(frozen=True, slots=True)
class PreparedCredential:
    """A token and its code, minted and hashed, **before anybody asks whether
    they will be used**.

    Minting and hashing are the expensive half of issuing one — the code's hash
    is the password hasher's — so a flow that must answer identically for an
    address nobody holds prepares one either way and throws it away: the answer
    then takes as long whether or not an account was found.
    """

    token: str
    code: str
    token_hash: str
    code_hash: str


@final
@dataclass(frozen=True, slots=True)
class ClaimTicket:
    """What a correct code is exchanged for: a secret the password is set with,
    and how many seconds it lasts."""

    ticket: str
    expires_in: int


class OneTimeCredentials:
    def __init__(
        self,
        *,
        store: OneTimeCredentialStore,
        secrets: CredentialSecrets,
        hasher: PasswordHasher,
    ) -> None:
        self._store = store
        self._secrets = secrets
        self._hasher = hasher

    def prepare(self) -> PreparedCredential:
        token = self._secrets.mint()
        code = code_for(token)
        return PreparedCredential(
            token=token,
            code=code,
            token_hash=digest_of(token),
            code_hash=self._hasher.hash(code),
        )

    async def issue(
        self,
        prepared: PreparedCredential,
        *,
        purpose: CredentialPurpose,
        audience: Audience,
        subject_id: UUID,
        email: str,
        now: Instant,
    ) -> OneTimeCredential:
        """Store ``prepared`` as the credential for ``subject_id``.

        **A newer credential retires the older ones for the same thing**: a
        second *Forgot password?*, or a resent invitation, leaves exactly one
        link and one code that work — the newest — and the older ones read
        *expired*.
        """

        for older in await self._store.live_for(
            subject_id, purpose=purpose, audience=audience, now=now
        ):
            older.retire(now=now)
            await self._store.save(older)
        credential = OneTimeCredential.issue(
            credential_id=new_uuid(),
            purpose=purpose,
            audience=audience,
            subject_id=subject_id,
            email=email,
            token_hash=prepared.token_hash,
            code_hash=prepared.code_hash,
            now=now,
        )
        await self._store.add(credential)
        return credential

    async def issued_since(
        self,
        email: str,
        *,
        purpose: CredentialPurpose,
        audience: Audience,
        since: Instant,
    ) -> int:
        """How many of this kind went to this address since ``since`` — what a
        throttle counts."""

        return len(
            await self._store.issued_to(
                email, purpose=purpose, audience=audience, since=since
            )
        )

    async def claim(
        self,
        *,
        email: str,
        code: str,
        purpose: CredentialPurpose,
        audience: Audience,
        now: Instant,
    ) -> ClaimTicket:
        """Exchange a correct code for a ticket.

        **Only the right code learns the credential's standing.** A wrong one —
        and a code for an address nothing was sent to — is ``code_incorrect``
        and nothing else, so the claim cannot be used to learn that an address
        has an account. A wrong code counts against every credential of this
        kind still live for that address; the fifth locks each.

        The caller commits whether this returns or raises: a wrong code that was
        not recorded would be a guess that cost nothing.
        """

        typed = TypedCode(code).value
        candidates = await self._store.issued_to(
            email,
            purpose=purpose,
            audience=audience,
            since=instant(now - CLAIM_LOOKBACK),
        )
        if not candidates:
            # The same hashing a comparison would have cost, so that *nothing
            # was ever sent here* takes as long to answer as *wrong code*.
            self._hasher.hash(typed)
            raise CredentialCodeIncorrect()

        for candidate in candidates:
            if not self._hasher.verify(typed, candidate.code_hash):
                continue
            candidate.refuse_unless_valid(now=now)
            ticket = self._secrets.mint()
            candidate.grant_ticket(digest_of(ticket), now=now)
            await self._store.save(candidate)
            return ClaimTicket(
                ticket=ticket, expires_in=candidate.ticket_seconds_left(now=now)
            )

        for candidate in candidates:
            if candidate.standing(now=now) is Standing.VALID:
                candidate.record_wrong_code()
                await self._store.save(candidate)
        raise CredentialCodeIncorrect()

    async def redeemable(
        self,
        *,
        token: Optional[str],
        ticket: Optional[str],
        purpose: CredentialPurpose,
        audience: Audience,
        now: Instant,
    ) -> OneTimeCredential:
        """The credential a link or a ticket opens, if it may be used now.

        A link or a ticket this surface did not issue for this purpose is
        ``credential_not_found`` — a player's link presented to the club website
        included. Otherwise the credential's own refusals come first, and a
        ticket's lapse only after them: a used credential is *used* whatever its
        ticket says.
        """

        if token is not None:
            credential = await self._store.by_token_hash(digest_of(token))
        elif ticket is not None:
            credential = await self._store.by_ticket_hash(digest_of(ticket))
        else:
            raise CredentialNotFound()
        if (
            credential is None
            or credential.purpose is not purpose
            or credential.audience is not audience
        ):
            raise CredentialNotFound()
        credential.refuse_unless_valid(now=now)
        if token is None:
            credential.refuse_unless_ticket_lasts(now=now)
        return credential

    async def use(self, credential: OneTimeCredential, *, now: Instant) -> None:
        credential.use(now=now)
        await self._store.save(credential)
