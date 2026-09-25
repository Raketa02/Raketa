"""*Forgot password?*: ask, claim a code, set a new password — **on one surface**.

Each use case is built once per audience (``docs/adr/0185`` §6), exactly as
the refresh and the sign-out are: the player app recovers Users and the club
website recovers Club accounts, through that audience's ``PasswordAccounts``,
and a credential issued on one surface opens nothing on the other — even for an
email both identities share.

1. **Asking** answers identically whether or not the address has an account
   (``docs/adr/0184`` §5), and is throttled per address the same way. The
   email is written to the mail queue in the request's own transaction; nothing
   here sends.
2. **Claiming** exchanges the emailed code for a short-lived ticket.
3. **Setting a new password**, by the link's token or by the ticket, follows the
   password rule every account has, **signs out everywhere** (``docs/adr/0185``
   §7) and signs this session in — in one transaction, so a password that
   changed without its sessions ending cannot be committed, and neither can a
   new session without the password it was opened with.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.application.ports import MailQueue, UnitOfWork
from app.kernel import Clock, instant
from app.modules.auth.application.one_time_credentials import (
    ClaimTicket,
    OneTimeCredentials,
)
from app.modules.auth.application.reset_email import reset_email
from app.modules.auth.application.sign_out_everywhere import SignOutEverywhere
from app.modules.auth.application.token_rotation import TokenPair, TokenRotator
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.errors import CredentialCodeIncorrect
from app.modules.auth.domain.one_time_credential import CredentialPurpose
from app.modules.auth.domain.password_reset import (
    RESET_REQUEST_WINDOW,
    RESET_REQUESTS_PER_WINDOW,
    ResetPage,
)
from app.modules.auth.domain.ports import PasswordAccounts, PasswordHasher
from app.modules.users.domain.errors import PasswordTooWeak
from app.modules.users.domain.value_objects import Email, RawPassword

_PURPOSE = CredentialPurpose.FORGOT_PASSWORD


@dataclass(frozen=True)
class ClaimPasswordResetCommand:
    email: str
    code: str


@dataclass(frozen=True)
class SetNewPasswordCommand:
    """Exactly one of ``token`` and ``ticket``: the link, or a claimed code."""

    password: str
    token: Optional[str] = None
    ticket: Optional[str] = None


class RequestPasswordReset:
    """Email a link and a code to the account behind an address, if there is one.

    ``reset_page`` is the page that sets the new password — the public site's
    for the player app, the club website's for a club.
    """

    def __init__(
        self,
        *,
        audience: Audience,
        accounts: PasswordAccounts,
        credentials: OneTimeCredentials,
        mail: MailQueue,
        reset_page: ResetPage,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._audience = audience
        self._accounts = accounts
        self._credentials = credentials
        self._mail = mail
        self._reset_page = reset_page
        self._uow = uow
        self._clock = clock

    async def execute(self, email: str) -> None:
        """Returns nothing, and returns it the same way for everybody."""

        now = self._clock.now()
        # Before the lookup, whoever asked: the hashing is most of the cost of
        # issuing one, so an address with no account takes as long to answer.
        prepared = self._credentials.prepare()
        try:
            address = Email(email).value
        except ValueError:
            return
        account = await self._accounts.recoverable(address)
        if account is None:
            return
        sent_lately = await self._credentials.issued_since(
            account.email,
            purpose=_PURPOSE,
            audience=self._audience,
            since=instant(now - RESET_REQUEST_WINDOW),
        )
        if sent_lately >= RESET_REQUESTS_PER_WINDOW:
            return
        await self._credentials.issue(
            prepared,
            purpose=_PURPOSE,
            audience=self._audience,
            subject_id=account.id,
            email=account.email,
            now=now,
        )
        await self._mail.enqueue(
            reset_email(
                audience=self._audience,
                to=account.email,
                link=self._reset_page.link_to(prepared.token),
                code=prepared.code,
            ),
            at=now,
        )
        await self._uow.commit()


class ClaimPasswordReset:
    """A correct code for an address, exchanged for a ticket."""

    def __init__(
        self,
        *,
        audience: Audience,
        credentials: OneTimeCredentials,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._audience = audience
        self._credentials = credentials
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ClaimPasswordResetCommand) -> ClaimTicket:
        try:
            address = Email(command.email).value
        except ValueError:
            raise CredentialCodeIncorrect() from None
        try:
            ticket = await self._credentials.claim(
                email=address,
                code=command.code,
                purpose=_PURPOSE,
                audience=self._audience,
                now=self._clock.now(),
            )
        except CredentialCodeIncorrect:
            # Committed before the refusal leaves: a wrong code that was not
            # counted would be a guess that cost nothing.
            await self._uow.commit()
            raise
        await self._uow.commit()
        return ticket


class SetNewPassword:
    """The new password, set by the link or by a claimed code — and every other
    session this account holds on this surface, ended."""

    def __init__(
        self,
        *,
        audience: Audience,
        accounts: PasswordAccounts,
        credentials: OneTimeCredentials,
        sign_out_everywhere: SignOutEverywhere,
        hasher: PasswordHasher,
        rotator: TokenRotator,
        clock: Clock,
    ) -> None:
        self._audience = audience
        self._accounts = accounts
        self._credentials = credentials
        self._sign_out_everywhere = sign_out_everywhere
        self._hasher = hasher
        self._rotator = rotator
        self._clock = clock

    async def execute(self, command: SetNewPasswordCommand) -> TokenPair:
        # The rule first: a password that is refused must not spend the link.
        try:
            password = RawPassword(command.password)
        except ValueError:
            raise PasswordTooWeak() from None

        now = self._clock.now()
        credential = await self._credentials.redeemable(
            token=command.token,
            ticket=command.ticket,
            purpose=_PURPOSE,
            audience=self._audience,
            now=now,
        )
        await self._accounts.set_password(
            credential.subject_id,
            password_hash=self._hasher.hash(password.value),
            at=now,
        )
        await self._sign_out_everywhere.execute(
            credential.subject_id, audience=self._audience, now=now
        )
        await self._credentials.use(credential, now=now)
        # The one commit, and the session this reset signs in. Its token is
        # issued after `now` on the same clock, so it survives the instant it
        # was opened under (``docs/adr/0185`` §7).
        return await self._rotator.issue_pair(
            credential.subject_id, audience=self._audience
        )
