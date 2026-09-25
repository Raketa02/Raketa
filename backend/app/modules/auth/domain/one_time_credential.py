"""A one-time credential: a link and a code that open one thing, once, for a while.

**One mechanism for everything** (``docs/adr/0184`` §3): an administrator's
invitation, the club's reset of one, and everybody's *Forgot password?* are the
same thing with three lifetimes. Each is a **link token** and an **8-character
code** issued together, and:

- **both are stored hashed** — the server only ever has to recognise them;
- **using either burns both** — setting the password is the use, and a used
  credential never reopens;
- **it expires** at its purpose's lifetime;
- **five wrong codes lock it**, link included.

**Claiming by email and code returns a short-lived ticket**, and the password is
then set with the ticket — so guessing is bounded to the one place that counts
the guesses. A claim is not a use: the code can be claimed again, which replaces
the ticket, until a password is set.

**It lives in a plain table and never in an event** (``docs/adr/0184`` §3–§4). A
credential is a secret with a lifetime; an event is kept for ever and replayed,
and a code's hash kept for ever is a code that can be cracked offline for ever.
That is also why nothing here records an event: *that* a reset was asked for is
not a fact any context reads, and *what* opens it may never be written where an
event would be.

**Its standing is derived, never stored**, from the clock and four facts —
used, wrong codes, the deadline, and nothing else — in one order, so a used
credential reads *used* whatever else is true of it.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Final, Mapping, Optional
from uuid import UUID

from app.kernel import Instant, instant
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.errors import (
    CredentialExpired,
    CredentialLocked,
    CredentialUsed,
    TicketExpired,
)


class CredentialPurpose(str, Enum):
    """What a credential opens, which decides how long it lives."""

    INVITATION = "invitation"
    CLUB_RESET = "club_reset"
    FORGOT_PASSWORD = "forgot_password"


#: How long each kind of credential lives (``docs/adr/0184`` §3). Domain, not
#: configuration: *valid for one hour* is written in the email a person reads.
LIFETIMES: Final[Mapping[CredentialPurpose, timedelta]] = {
    CredentialPurpose.INVITATION: timedelta(hours=72),
    CredentialPurpose.CLUB_RESET: timedelta(hours=72),
    CredentialPurpose.FORGOT_PASSWORD: timedelta(hours=1),
}

#: Wrong codes a credential survives. The fifth locks it.
MAX_WRONG_CODES: Final = 5

#: How long a claim's ticket lasts: long enough to type a new password twice,
#: and never past the credential's own deadline.
TICKET_LIFETIME: Final = timedelta(minutes=15)


class Standing(str, Enum):
    """What a credential is, read now. The public pages show all four
    (``docs/adr/0184`` §3), and a claim or a use refuses on the last three."""

    VALID = "valid"
    EXPIRED = "expired"
    USED = "used"
    LOCKED = "locked"


def digest_of(secret: str) -> str:
    """How a link token or a ticket is stored and looked up.

    SHA-256 and unsalted, because each is 256 random bits: there is nothing to
    guess, so the hash only has to be a lookup key that is not the secret. The
    **code** is the one secret small enough to guess, and it is hashed with the
    password hasher instead.
    """

    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


@dataclass
class OneTimeCredential:
    """One issued credential, as its row holds it.

    ``subject_id`` is whatever the credential opens — a User or a Club account
    for a reset, an Administrator for an invitation — and ``audience`` says which
    surface may use it, so a player's code is refused on the club website even
    for an email both identities share (``docs/adr/0185`` §6). ``email`` is the
    address a claim names, as the account holds it.
    """

    id: UUID
    purpose: CredentialPurpose
    audience: Audience
    subject_id: UUID
    email: str
    token_hash: str
    code_hash: str
    issued_at: Instant
    expires_at: Instant
    wrong_codes: int = 0
    used_at: Optional[Instant] = None
    ticket_hash: Optional[str] = None
    ticket_expires_at: Optional[Instant] = None

    @classmethod
    def issue(
        cls,
        *,
        credential_id: UUID,
        purpose: CredentialPurpose,
        audience: Audience,
        subject_id: UUID,
        email: str,
        token_hash: str,
        code_hash: str,
        now: Instant,
    ) -> "OneTimeCredential":
        return cls(
            id=credential_id,
            purpose=purpose,
            audience=audience,
            subject_id=subject_id,
            email=email,
            token_hash=token_hash,
            code_hash=code_hash,
            issued_at=now,
            expires_at=instant(now + LIFETIMES[purpose]),
        )

    def standing(self, *, now: Instant) -> Standing:
        if self.used_at is not None:
            return Standing.USED
        if self.wrong_codes >= MAX_WRONG_CODES:
            return Standing.LOCKED
        if now >= self.expires_at:
            return Standing.EXPIRED
        return Standing.VALID

    def refuse_unless_valid(self, *, now: Instant) -> None:
        """Refuse a credential that can no longer be used, in its standing's
        own words: *used*, *locked*, *expired*."""

        standing = self.standing(now=now)
        if standing is Standing.USED:
            raise CredentialUsed()
        if standing is Standing.LOCKED:
            raise CredentialLocked()
        if standing is Standing.EXPIRED:
            raise CredentialExpired()

    def record_wrong_code(self) -> None:
        """One more wrong code. The fifth locks it; the link with it."""

        self.wrong_codes += 1

    def grant_ticket(self, ticket_hash: str, *, now: Instant) -> None:
        """A claim's ticket, replacing any earlier one. It never outlives the
        credential it was claimed from."""

        self.ticket_hash = ticket_hash
        self.ticket_expires_at = min(instant(now + TICKET_LIFETIME), self.expires_at)

    def refuse_unless_ticket_lasts(self, *, now: Instant) -> None:
        """A ticket presented after its minutes: the code still works, and
        claiming it again is a fresh one."""

        if self.ticket_expires_at is None or now >= self.ticket_expires_at:
            raise TicketExpired()

    def ticket_seconds_left(self, *, now: Instant) -> int:
        if self.ticket_expires_at is None:
            return 0
        return max(0, int((self.ticket_expires_at - now).total_seconds()))

    def use(self, *, now: Instant) -> None:
        """The password was set: the link, the code and the ticket are spent.

        The ticket's hash is kept, so a ticket presented again is told *used*
        like the link and the code are, rather than *never issued*."""

        self.used_at = now

    def retire(self, *, now: Instant) -> None:
        """A newer credential for the same thing was issued: this one ends now
        and reads *expired*, as a credential whose time ran out does — the
        person holding it has a newer email, and *ask again* is still true."""

        if now < self.expires_at:
            self.expires_at = now
