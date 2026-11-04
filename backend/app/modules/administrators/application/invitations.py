"""The person's side of an invitation, on the player surface and on the public
site's invitation page (``docs/adr/0184`` §2–§3, ``docs/adr/0187`` §4).

**A new person** — or an account a club has cleared — sets a password through
the email's link, or through the code claimed for a ticket; that opens or
recovers the account, makes the Administrator *active*, and signs them in —
**in the app**; the public page does all of it but the last, since it holds no
session. The four refusals a person is shown are the credential mechanism's
own: a wrong code, *expired* (ask the club to send a new one), *used*, and
*locked*.

**An existing account** accepts from the app, signed in, on the account whose
email the invitation names — and a code or a link that reaches an address which
has since become such an account is answered *sign in to accept*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.administrators.application.commands import (
    ClaimInvitationCommand,
    SetInvitationPasswordCommand,
)
from app.modules.administrators.application.sending import (
    ADMINISTRATOR_CREDENTIALS,
    AUDIENCE,
    InvitationSender,
)
from app.modules.administrators.domain.administrator import (
    Administrator,
    AdministratorState,
)
from app.modules.administrators.domain.errors import (
    InvitationNotFound,
    InvitationNotPending,
    SignInToAccept,
)
from app.modules.administrators.domain.ports import (
    AccountHolders,
    AdministratorRepository,
    ClubNames,
    club_name_of,
)
from app.modules.auth.application.one_time_credentials import (
    ClaimTicket,
    OneTimeCredentials,
)
from app.modules.auth.application.sign_out_everywhere import SignOutEverywhere
from app.modules.auth.application.token_rotation import TokenPair, TokenRotator
from app.modules.auth.domain.credential_code import code_for
from app.modules.auth.domain.errors import (
    CredentialCodeIncorrect,
    CredentialNotFound,
)
from app.modules.auth.domain.one_time_credential import (
    OneTimeCredential,
    Standing,
)
from app.modules.auth.domain.ports import PasswordHasher
from app.modules.users.domain.errors import PasswordTooWeak
from app.modules.users.domain.value_objects import Email, RawPassword


async def _the_administrator(
    administrators: AdministratorRepository, credential: OneTimeCredential
) -> Administrator:
    administrator = await administrators.load(credential.subject_id)
    if administrator is None:
        # An administrator credential is issued for an Administrator in the
        # same transaction that records it, and nothing deletes one.
        raise RuntimeError(
            f"credential {credential.id} names administrator "
            f"{credential.subject_id}, which has no stream"
        )
    return administrator


async def _refuse_an_account_that_signs_in(
    accounts: AccountHolders, administrator: Administrator
) -> None:
    holder = await accounts.holder_of(administrator.email)
    if holder is not None and holder.can_sign_in:
        raise SignInToAccept()


class ClaimInvitation:
    """*Have an invitation code?*: an email and a code, exchanged for a
    ticket the password is then set with."""

    def __init__(
        self,
        *,
        credentials: OneTimeCredentials,
        administrators: AdministratorRepository,
        accounts: AccountHolders,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._credentials = credentials
        self._administrators = administrators
        self._accounts = accounts
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ClaimInvitationCommand) -> ClaimTicket:
        try:
            address = Email(command.email).value
        except ValueError:
            raise CredentialCodeIncorrect() from None
        now = self._clock.now()
        try:
            credential = await self._credentials.verify_code(
                email=address,
                code=command.code,
                purposes=ADMINISTRATOR_CREDENTIALS,
                audience=AUDIENCE,
                now=now,
            )
        except CredentialCodeIncorrect:
            # Committed before the refusal leaves: a wrong code that was not
            # counted would be a guess that cost nothing.
            await self._uow.commit()
            raise
        # Asked only now, of somebody holding the right code: said to anybody
        # else, it would tell them the address has an account.
        await _refuse_an_account_that_signs_in(
            self._accounts,
            await _the_administrator(self._administrators, credential),
        )
        ticket = await self._credentials.grant_ticket(credential, now=now)
        await self._uow.commit()
        return ticket


class _InvitationPassword:
    """*Set your password*'s rules, **wherever it is pressed** — in the app, or
    on the public site's invitation page — so the two cannot come to two
    answers about one link.

    **For a new person it opens the account** — no player name (the name the
    club typed stays on the Administrator, ``docs/adr/0199`` §4), no nickname,
    no Adult attestation (``docs/adr/0185`` §5); **for an account
    a club cleared it sets that account's password** and signs its other
    sessions out. Either way the Administrator is *active* and the credential
    spent. Nothing is committed: what ends the act — a session, or none — is
    the caller's.
    """

    def __init__(
        self,
        *,
        credentials: OneTimeCredentials,
        administrators: AdministratorRepository,
        accounts: AccountHolders,
        sign_out_everywhere: SignOutEverywhere,
        hasher: PasswordHasher,
        clock: Clock,
    ) -> None:
        self._credentials = credentials
        self._administrators = administrators
        self._accounts = accounts
        self._sign_out_everywhere = sign_out_everywhere
        self._hasher = hasher
        self._clock = clock

    async def set(self, command: SetInvitationPasswordCommand) -> UUID:
        """The account whose password was set."""

        # The rule first: a password that is refused must not spend the link.
        try:
            password = RawPassword(command.password)
        except ValueError:
            raise PasswordTooWeak() from None

        now = self._clock.now()
        credential = await self._credentials.redeemable(
            token=command.token,
            ticket=command.ticket,
            purposes=ADMINISTRATOR_CREDENTIALS,
            audience=AUDIENCE,
            now=now,
        )
        administrator = await _the_administrator(self._administrators, credential)
        password_hash = self._hasher.hash(password.value)
        holder = await self._accounts.holder_of(administrator.email)
        if holder is None:
            account_id = await self._accounts.open_account(
                email=administrator.email,
                password_hash=password_hash,
                at=now,
            )
        elif holder.can_sign_in:
            raise SignInToAccept()
        else:
            account_id = holder.id
            await self._accounts.set_password(
                account_id, password_hash=password_hash, at=now
            )
            await self._sign_out_everywhere.execute(
                account_id, audience=AUDIENCE, now=now
            )

        administrator.accept(account_id=account_id, now=now)
        await self._administrators.save(administrator)
        await self._credentials.use(credential, now=now)
        return account_id


class SetInvitationPassword:
    """Set a password by the email's link or a claimed ticket, **in the app** —
    and this session is signed in, in the same transaction."""

    def __init__(
        self,
        *,
        credentials: OneTimeCredentials,
        administrators: AdministratorRepository,
        accounts: AccountHolders,
        sign_out_everywhere: SignOutEverywhere,
        hasher: PasswordHasher,
        rotator: TokenRotator,
        clock: Clock,
    ) -> None:
        self._password = _InvitationPassword(
            credentials=credentials,
            administrators=administrators,
            accounts=accounts,
            sign_out_everywhere=sign_out_everywhere,
            hasher=hasher,
            clock=clock,
        )
        self._rotator = rotator

    async def execute(self, command: SetInvitationPasswordCommand) -> TokenPair:
        account_id = await self._password.set(command)
        # The one commit, and the session this signs in: issued after `now` on
        # the same clock, so it survives the instant it was opened under
        # (``docs/adr/0185`` §7).
        return await self._rotator.issue_pair(account_id, audience=AUDIENCE)


class SetInvitationPasswordWithoutSigningIn:
    """Set a password by the email's link **on the public site's invitation
    page**: the same rules and the same results as the app's, and **no session
    at all** — the site holds none (``docs/adr/0187`` §4), so the person opens
    Raketa and signs in with the password they have just chosen."""

    def __init__(
        self,
        *,
        credentials: OneTimeCredentials,
        administrators: AdministratorRepository,
        accounts: AccountHolders,
        sign_out_everywhere: SignOutEverywhere,
        hasher: PasswordHasher,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._password = _InvitationPassword(
            credentials=credentials,
            administrators=administrators,
            accounts=accounts,
            sign_out_everywhere=sign_out_everywhere,
            hasher=hasher,
            clock=clock,
        )
        self._uow = uow

    async def execute(self, command: SetInvitationPasswordCommand) -> None:
        await self._password.set(command)
        await self._uow.commit()


@final
@dataclass(frozen=True, slots=True)
class OpenedInvitation:
    """What an invitation's link opens, read before anything is set: whom it
    greets, for which club, whether it still works — and, **while it does**,
    the code its email carries, recomputed from the link (``code_for``) because
    the server keeps only the code's hash. Whoever holds the link can already
    use it; the code is what the public page prints for *after you install,
    open Raketa and enter this code* (``docs/adr/0187`` §4)."""

    email: str
    name: str
    club_name: str
    standing: Standing
    code: Optional[str]


class ReadInvitationByToken:
    """The invitation a link opens, **whatever its standing** — what *Set your
    password* locks its email field to. A link this surface never issued is
    ``credential_not_found``, as it is everywhere else."""

    def __init__(
        self,
        *,
        credentials: OneTimeCredentials,
        administrators: AdministratorRepository,
        clubs: ClubNames,
        clock: Clock,
    ) -> None:
        self._credentials = credentials
        self._administrators = administrators
        self._clubs = clubs
        self._clock = clock

    async def execute(self, token: str) -> OpenedInvitation:
        credential = await self._credentials.opened_by(
            token, purposes=ADMINISTRATOR_CREDENTIALS, audience=AUDIENCE
        )
        if credential is None:
            raise CredentialNotFound()
        administrator = await _the_administrator(self._administrators, credential)
        standing = credential.standing(now=self._clock.now())
        return OpenedInvitation(
            email=administrator.email.value,
            name=administrator.name.value,
            club_name=await club_name_of(self._clubs, administrator.club_id),
            standing=standing,
            code=code_for(token) if standing is Standing.VALID else None,
        )


class AcceptInvitation:
    """**Accept**, on the invitation sheet: the signed-in account whose email
    the invitation names takes it up, and the Administrator is *active*
    (``docs/adr/0184`` §2). No password is involved. Accepting again is the
    same answer."""

    def __init__(
        self,
        *,
        administrators: AdministratorRepository,
        sender: InvitationSender,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._administrators = administrators
        self._sender = sender
        self._uow = uow
        self._clock = clock

    async def execute(
        self, *, account_id: UUID, email: Email, administrator_id: UUID
    ) -> None:
        administrator = await self._administrators.load(administrator_id)
        if (
            administrator is None
            or administrator.email != email
            or administrator.state is AdministratorState.REMOVED
        ):
            # Somebody else's, a removed one and one that never was are one
            # answer: an account learns nothing about invitations not its own.
            raise InvitationNotFound()
        now = self._clock.now()
        try:
            administrator.accept(account_id=account_id, now=now)
        except InvitationNotPending:
            raise InvitationNotFound() from None
        await self._administrators.save(administrator)
        # A link still in the inbox from a new-person email, or a club's reset,
        # opens nothing once the app is the way in.
        await self._sender.retire(administrator, now=now)
        await self._uow.commit()
